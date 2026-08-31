import logging
import os

import tablib
import sqlalchemy
from auth0.v2.management import Auth0

from . import myemail
from .logging_config import configure_logging
import traceback  # Just to show the full traceback
from psycopg2 import errors

InFailedSqlTransaction = errors.lookup('25P02')
UniqueViolation = errors.lookup('23505')

# importing module

# Configure logging once for the application.
configure_logging()
logger = logging.getLogger(__name__)

# Auth0 API Client
auth0_domain = os.environ['AUTH0_DOMAIN']
auth0_token = os.environ['AUTH0_JWT_V2_TOKEN']
auth0 = Auth0(auth0_domain, auth0_token)

# Database connection.
engine = sqlalchemy.create_engine(os.environ['DATABASE_URL'])
conn = engine.connect()


# Storage Models
# Note: Some of these are a little fancy (send email and such).
# --------------


class Note:
    """A generic note of thankfulness.

    Attributes:
        body (str): The content of the note.
        byline (str): The author/display name.
        inbox (Inbox): The associated Inbox instance.
        archived (bool): Whether the note is archived.
        uuid (str): The database-assigned UUID.
        timestamp (datetime): When the note was created.
        audio_path (str): Optional stored filename for voice note.
    """

    def __init__(self):
        """Create an empty Note instance."""
        self.body = None
        self.byline = None
        self.inbox = None
        self.archived = None
        self.uuid = None
        self.timestamp = None
        self.audio_path = None

    def __repr__(self):
        """Return a short representation for debugging."""
        return (
            f"<Note size={len(self.body)}>"
            if self.body
            else "<Note is (empty)>".strip()
        )

    @classmethod
    def fetch(cls, uuid):
        """Retrieve a Note from the database by UUID.

        Args:
            uuid (str): The UUID of the note to fetch.

        Returns:
            Note: A Note instance populated with stored values.

        Raises:
            IndexError: If no row is found for the given UUID.
        """
        self = cls()
        q = sqlalchemy.text("SELECT * FROM notes WHERE uuid=:uuid")
        r = conn.execute(q, uuid=uuid).fetchall()
        self.body = r[0]['body']
        self.byline = r[0]['byline']
        self.uuid = uuid
        return self

    @classmethod
    def from_inbox(
        cls,
        inbox,
        body,
        byline,
        archived=False,
        uuid=None,
        timestamp=None,
        audio_path=None,
    ):
        """Instantiate a Note associated with a given inbox slug.

        Args:
            inbox (str): Inbox slug.
            body (str): Note content.
            byline (str): Author/display name.
            archived (bool): Whether the note is archived (default False).
            uuid (str|None): Optional existing UUID.
            timestamp (datetime|None): Optional timestamp.
            audio_path (str|None): Optional filename for stored audio.

        Returns:
            Note: New Note instance.
        """
        self = cls()

        self.body = body
        self.byline = byline
        self.uuid = uuid
        self.archived = archived
        self.inbox = Inbox(inbox)
        self.timestamp = timestamp
        self.audio_path = audio_path

        return self

    @classmethod
    def does_exist(cls, uuid):
        """Check whether a note exists in the database.

        Args:
            uuid (str): UUID to check.

        Returns:
            bool: True if the note exists, False otherwise.
        """
        q = sqlalchemy.text('SELECT * from notes where uuid = :uuid')
        r = conn.execute(q, uuid=uuid).fetchall()
        return bool(len(r))

    def store(self):
        """Persist the Note to the database.

        Handles presence/absence of an audio_path column in the database.
        Sets self.uuid to the database-generated UUID on success.

        Raises:
            Exception: Propagates database errors after logging.
        """
        try:
            params = {
                'body': self.body,
                'byline': self.byline,
                'inbox': self.inbox.auth_id,
            }
            base_query = '''
                INSERT INTO notes (body, byline, inboxes_auth_id)
                VALUES (:body, :byline, :inbox)
                RETURNING uuid
            '''
            q = base_query

            if self.audio_path:
                check_column = sqlalchemy.text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name='notes'
                        AND column_name='audio_path'
                    );
                """
                )
                has_audio_column = conn.execute(check_column).scalar()

                if has_audio_column:
                    q = '''
                    INSERT INTO notes (body, byline, inboxes_auth_id, audio_path)
                    VALUES (:body, :byline, :inbox, :audio_path)
                    RETURNING uuid
                    '''
                    params['audio_path'] = self.audio_path
                else:
                    logger.info(
                        "Audio_path column absent; voice-note link is embedded in body"
                    )

            q = sqlalchemy.text(q)
            # Execute the query with parameters
            result = conn.execute(q, **params)
            # Assign the generated UUID from the database to this Note instance
            self.uuid = result.fetchone()['uuid']
            logger.info("Note stored with UUID: %s", self.uuid)
        except Exception as e:
            logger.error(f"Error storing note: {str(e)}")
            raise

    def archive(self):
        """Mark this note as archived in the database."""
        q = sqlalchemy.text("UPDATE notes SET archived = 't' WHERE uuid = :uuid")
        conn.execute(q, uuid=self.uuid)

    def notify(self, email_address, topic=None, audio_path=None):
        """Send an email notification for this note.

        Delegates to myemail.notify.

        Args:
            email_address (str): Recipient email address.
            topic (str|None): Optional topic for subject line.
            audio_path (str|None): Optional audio filename to include.
        """
        myemail.notify(self, email_address, topic, audio_path)


class Inbox:
    """A registered inbox for a given user (provided by Auth0).

    The Inbox is primarily identified by its slug and provides methods to
    query and manipulate user inbox state and notes.
    """

    def __init__(self, slug):
        """Create an Inbox wrapper for a slug.

        Args:
            slug (str): Inbox slug used in the database.
        """
        self.slug = slug

    @property
    def auth_id(self):
        """Return the Auth0 auth_id associated with this inbox.

        Looks up the inbox row by slug and returns the auth_id column.

        Returns:
            str: Auth0 user id.
        """
        q = sqlalchemy.text("SELECT * FROM inboxes WHERE slug=:inbox")
        r = conn.execute(q, inbox=self.slug).fetchall()
        return r[0]['auth_id']

    @classmethod
    def is_linked(cls, auth_id):
        """Check whether an Auth0 user id is linked to any inbox.

        Args:
            auth_id (str): Auth0 user id to check.

        Returns:
            bool: True if linked, False otherwise.
        """
        q = sqlalchemy.text('SELECT * from inboxes where auth_id = :auth_id')
        r = conn.execute(q, auth_id=auth_id).fetchall()
        return bool(len(r))

    @classmethod
    def link_or_create(cls, auth_id, nickname, email):
        q = sqlalchemy.text('SELECT slug, email FROM inboxes WHERE auth_id = :auth_id')
        row = conn.execute(q, auth_id=auth_id).fetchone()
        if row:
            existing_slug = row['slug']
            existing_email = row['email']
            # If they changed their email on GitHub/Auth0, update it silently
            if existing_email != email:
                u = sqlalchemy.text(
                    'UPDATE inboxes SET email = :email WHERE auth_id = :auth_id'
                )
                conn.execute(u, email=email, auth_id=auth_id)
            return existing_slug
        base_slug = nickname
        slug_to_try = base_slug
        counter = 1
        # Resolve nickname collisions by appending a counter
        while cls.does_exist(slug_to_try):
            slug_to_try = f"{base_slug}-{counter}"
            counter += 1
        cls.store(slug_to_try, auth_id, email)
        return slug_to_try

    @classmethod
    def store(cls, slug, auth_id, email):
        """Store a mapping between an inbox slug and an Auth0 user/email.

        Args:
            slug (str): Desired inbox slug.
            auth_id (str): Auth0 user id.
            email (str): Email address for the inbox.

        Returns:
            Inbox: The created Inbox instance or existing slug wrapper.

        Notes:
            Logs and continues on UniqueViolation to avoid raising on duplicates.
        """
        try:
            q = sqlalchemy.text(
                '''
                INSERT into inboxes
                    (slug, auth_id, email)
                VALUES
                    (:slug, :auth_id, :email)
            '''
            )
            conn.execute(q, slug=slug, auth_id=auth_id, email=email)

        except UniqueViolation:
            print('Duplicate record - ID already exist')
            logging.error("ID already exist")
        return cls(slug)

    @classmethod
    def does_exist(cls, slug):
        """Check whether an inbox with the given slug exists.

        Args:
            slug (str): Inbox slug to check.

        Returns:
            bool: True if the inbox exists, False otherwise.
        """
        q = sqlalchemy.text('SELECT * from inboxes where slug = :slug')
        r = conn.execute(q, slug=slug).fetchall()
        return bool(len(r))

    @classmethod
    def is_email_enabled(cls, slug):
        """Return whether outgoing emails are enabled for the inbox.

        Args:
            slug (str): Inbox slug.

        Returns:
            bool: True if email is enabled, False otherwise.
        """
        q = sqlalchemy.text('SELECT email_enabled FROM inboxes where slug = :slug')
        try:
            r = conn.execute(q, slug=slug).fetchall()
            return bool(r[0]['email_enabled'])
        except InFailedSqlTransaction:
            print(traceback.print_exc())
            logging.error(traceback.print_exc())
            return False

    @classmethod
    def disable_email(cls, slug):
        """Disable outgoing emails for the given inbox."""
        q = sqlalchemy.text(
            'update inboxes set email_enabled = false where slug = :slug'
        )
        conn.execute(q, slug=slug)

    @classmethod
    def enable_email(cls, slug):
        """Enable outgoing emails for the given inbox."""
        q = sqlalchemy.text(
            'update inboxes set email_enabled = true where slug = :slug'
        )
        conn.execute(q, slug=slug)

    @classmethod
    def is_enabled(cls, slug):
        """Return whether the inbox account is enabled.

        Args:
            slug (str): Inbox slug.

        Returns:
            bool: True if enabled, False otherwise.
        """
        q = sqlalchemy.text('SELECT enabled FROM inboxes where slug = :slug')
        try:
            r = conn.execute(q, slug=slug).fetchall()
            if not r[0]['enabled']:
                return False
            return bool(r[0]['enabled'])
        except InFailedSqlTransaction:
            print(traceback.print_exc())
            logging.error(traceback.print_exc())
            return False

    @classmethod
    def disable_account(cls, slug):
        """Disable the inbox account (sets enabled = false)."""
        q = sqlalchemy.text('update inboxes set enabled = false where slug = :slug')
        conn.execute(q, slug=slug)

    @classmethod
    def enable_account(cls, slug):
        """Enable the inbox account (sets enabled = true)."""
        q = sqlalchemy.text('update inboxes set enabled = true where slug = :slug')
        conn.execute(q, slug=slug)

    def submit_note(self, body, byline, audio_path=None):
        """Create and store a new note for this inbox.

        Args:
            body (str): Note content.
            byline (str): Author/display name.
            audio_path (str|None): Optional audio filename.

        Returns:
            Note: Stored Note instance (uuid will be set).
        """
        note = Note.from_inbox(self.slug, body, byline, audio_path=audio_path)
        note.store()
        return note

    @classmethod
    def get_email(cls, slug):
        """Return the email address associated with an inbox slug.

        Args:
            slug (str): Inbox slug.

        Returns:
            str: Email address from the inboxes table.
        """
        q = sqlalchemy.text('SELECT email FROM inboxes where slug = :slug')
        r = conn.execute(q, slug=slug).fetchall()
        return r[0]['email']

    @property
    def myemail(self):
        """Return the email address from Auth0 for this inbox's user.

        This property fetches the user record from Auth0 using auth_id
        and returns the user's email.
        """
        return auth0.users.get(self.auth_id)['email']
        # emailinfo = auth0.users.get(self.auth_id)['email']
        # print("myemail prop",emailinfo)
        # return emailinfo

    def notes(self, page, page_size):
        """Return paginated, non-archived notes for this inbox.

        Args:
            page (int): 1-based page number.
            page_size (int): Number of notes per page.

        Returns:
            dict: {
                "notes": list[Note],
                "total_notes": int,
                "page": int,
                "total_pages": int
            }
        """
        offset = (page - 1) * page_size
        count_query = sqlalchemy.text(
            """
            SELECT COUNT(*)
            FROM notes
            WHERE inboxes_auth_id = :auth_id
            AND archived = 'f'
        """
        )
        total_notes = conn.execute(count_query, auth_id=self.auth_id).scalar()
        query = sqlalchemy.text(
            """
            SELECT * FROM notes
            WHERE inboxes_auth_id = :auth_id AND archived = 'f'
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        """
        )
        result = conn.execute(
            query, auth_id=self.auth_id, limit=page_size, offset=offset
        ).fetchall()

        notes = [
            Note.from_inbox(
                self.slug,
                n["body"],
                n["byline"],
                n["archived"],
                n["uuid"],
                n["timestamp"],
            )
            for n in result
        ]

        return {
            "notes": notes,
            "total_notes": total_notes,
            "page": page,
            "total_pages": (total_notes + page_size - 1)
            // page_size,  # Calculate total pages
        }

    def search_notes(self, search_str, page, page_size):
        """Search notes in this inbox by body or byline with pagination.

        The search is case-insensitive and uses SQL LIKE matching.

        Args:
            search_str (str): Substring to search for.
            page (int): 1-based page number.
            page_size (int): Number of results per page.

        Returns:
            dict: {
                "notes": list[Note],
                "total_notes": int,
                "page": int,
                "total_pages": int
            }
        """
        offset = (page - 1) * page_size
        search_str_lower = search_str.lower()

        query = sqlalchemy.text(
            """
            SELECT *,
                COUNT(*) OVER() AS total_notes
            FROM notes
            WHERE (
                LOWER(body) LIKE '%' || :param || '%'
                OR LOWER(byline) LIKE '%' || :param || '%'
            )
            AND inboxes_auth_id = :auth_id
            AND archived = 'f'
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        """
        )
        # Execute the query with the search string and pagination parameters
        result = conn.execute(
            query,
            param=search_str_lower,
            auth_id=self.auth_id,
            limit=page_size,
            offset=offset,
        ).fetchall()

        notes = [
            Note.from_inbox(
                self.slug,
                n["body"],
                n["byline"],
                n["archived"],
                n["uuid"],
                n["timestamp"],
            )
            for n in result
        ]

        # Get total_notes from the first row, or 0 if no results
        total_notes = result[0]['total_notes'] if result else 0

        return {
            "notes": notes,
            "total_notes": total_notes,
            "page": page,
            "total_pages": (total_notes + page_size - 1)
            // page_size,  # Calculate total pages
        }

    def export(self, file_format):
        """Export all non-archived notes for this inbox in the given format.

        Args:
            file_format (str): Format supported by tablib (e.g. 'csv', 'xlsx').

        Returns:
            bytes|str: Exported data in the requested format.
        """
        q = sqlalchemy.text(
            "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 'f'"
        )
        r = conn.execute(q, auth_id=self.auth_id).fetchall()
        return tablib.Dataset(r).export(file_format)

    @property
    def archived_notes(self):
        """Return archived notes for this inbox in reverse-chronological order.

        Returns:
            list[Note]: Archived Note instances (most recent first).
        """
        q = sqlalchemy.text(
            "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 't'"
        )
        r = conn.execute(q, auth_id=self.auth_id).fetchall()

        notes = [
            Note.from_inbox(self.slug, n['body'], n['byline'], n['archived'], n['uuid'])
            for n in r
        ]
        return notes[::-1]
