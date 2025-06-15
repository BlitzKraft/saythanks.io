import os

import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail
from urllib.error import URLError
from flask import url_for, current_app, request

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

API_KEY = os.environ['SENDGRID_API_KEY']
sg = sendgrid.SendGridAPIClient(api_key=API_KEY)

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


def notify(note, email_address):
    """Use the note contents and a template, build a
    formatted message. Use sendgrid to deliver the formatted
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
    fails.
    """
    try:
        if not note.uuid:
            logging.error("Could not find UUID for note — link will be blank.")
            note_url = ''
        else:
            with current_app.app_context():
                note_url = url_for('share_note', uuid=note.uuid, _external=True)

        # Say 'someone' if the byline is empty.
        who = note.byline or 'someone'

        subject = 'saythanks.io: {} sent a note!'.format(who)
        message = TEMPLATE.format(note.body, note.byline, note_url)
        from_address = Email('no-reply@saythanks.io', name="SayThanks.io")
        to_address = Email(email_address)
        content = Content('text/html', message)

        mail = Mail(from_address, subject, to_address, content)
        response = sg.client.mail.send.post(request_body=mail.get())
    except URLError as e:
        logging.error("URL Error occurred "+ str(e))
        print(e)
    except Exception as e:
        logging.error("General Error occurred: " + str(e))
        print(e)
