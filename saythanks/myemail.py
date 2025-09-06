import os
import requests

from mailersend import emails
from urllib.error import URLError
from flask import url_for, current_app

# importing module
import logging

# Create and configure logger
logging.basicConfig(filename='Logfile.log',
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

# Creating an object
logger = logging.getLogger()

# Email Infrastructure
# --------------------

# Initialize MailerSend SDK
mailersend_api_key = os.getenv('MAILERSEND_API_KEY')
if not mailersend_api_key:
    logger.error("MAILERSEND_API_KEY environment variable not set")
    mailer = None
else:
    mailer = emails.NewEmail(mailersend_api_key)

TEMPLATE = """<div>{}
<br>
<br>
--{}
<br>
<br>
The public URL for this note is <a clicktracking=off href="{}">here</a> <br>
<br>
<br>
=========
<br>
<br>
This note of gratitude was brought to you by SayThanks.io.
<br>
<br>
A KennethReitz project, now maintained by KGiSL Edu (https://edu.kgisl.com).
</div>
"""


def notify(note, email_address, topic=None):
    """Use the note contents and a template, build a
    formatted message. Use MailerSend to deliver the formatted
    message as an email to the user.

    The email includes:
    - The note's body and byline.
    - A public URL for the note, allowing the user to share it with others.
        - If the note has a UUID, the URL is generated using Flask's `url_for`
        with the 'share_note' route.
        - If the note lacks a UUID, the URL field in the email will be left blank
        and an error is logged.

    Args:
        note: An object representing the note, expected to have 'body', 'byline',
            and 'uuid' attributes.
        email_address: The recipient's email address.

    The function logs errors if the note's UUID is missing or if sending the email
    fails but ensures the note is still saved even if email delivery fails.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # print("myemail:notify", topic) # Debugging line to check topic

    # Check if MailerSend is properly configured
    if mailer is None:
        logger.error("MailerSend not configured - email notification skipped")
        return False

    try:
        if not note.uuid:
            logging.error("Could not find UUID for note — link will be blank.")
            note_url = ''
        else:
            with current_app.app_context():
                note_url = url_for('share_note', uuid=note.uuid, _external=True)

        # Say 'someone' if the byline is empty.
        who = note.byline or 'someone'

        subject = f'saythanks.io: {who} sent a note!' if not topic \
            else f'saythanks.io: {who} sent a note about {topic}!'

        html_content = TEMPLATE.format(note.body, note.byline, note_url)
        # print("\n\n***html_content", html_content)  # Debugging line to check html_body
        plaintext_content = f"{note.body}\n\n--{note.byline or ''}\n\n{note_url}"

        mail_body = {}
        mailer.set_mail_from({"name": "SayThanks.io", "email": "no-reply@saythanks.io"}, mail_body)
        mailer.set_mail_to([{"email": email_address}], mail_body)
        mailer.set_subject(subject, mail_body)
        mailer.set_html_content(html_content, mail_body)
        mailer.set_plaintext_content(plaintext_content, mail_body)
        response = mailer.send(mail_body)
        logger.error(f"MailerSend SDK send response: {response}")

        # Handle successful responses
        if hasattr(response, 'status_code'):
            if response.status_code == 202:
                logger.error(f"Email queued successfully for delivery to {email_address}")
                return True
            elif response.status_code == 200:
                logger.info(f"Email sent successfully to {email_address}")
                return True
            elif response.status_code >= 400:
                logger.error(f"MailerSend API error {response.status_code}: {response.text if hasattr(response, 'text') else 'Unknown error'}")
                return False
        else:
            logger.info(f"Email request submitted successfully to {email_address}")
            return True

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Network connection error when sending email: {str(e)}")
        logger.error("Check your internet connection and MAILERSEND_API_KEY configuration")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error when sending email: {str(e)}")
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error when sending email: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        return False
    except URLError as e:
        logger.error(f"URL Error occurred: {str(e)}")
        print(e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error when sending email: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        print(e)
        return False