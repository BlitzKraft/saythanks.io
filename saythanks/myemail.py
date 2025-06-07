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
The public URL for this note is <a href="{}">here</a> <br>
or {}. 
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

    Also include the public URL for the note, so that
    the user can share it with others.
    """
    try:
        if not note.uuid:
            logging.error("Could not find UUID for note — link will be blank.")
            note_url = ''
        else:
            with current_app.app_context():
                note_url = url_for('share_note', uuid=note.uuid, _external=True)

            # server_name = os.environ.get('SERVER_NAME', 'http://localhost:5000')
            # note_url2 = "https://"+server_name + "/note/" + str(note.uuid) 
            base_url = request.url_root  
            note_url2 = base_url + "note/" + str(note.uuid) 
            logging.error("note_url2: " + note_url2)
        
        # Say 'someone' if the byline is empty.
        who = note.byline or 'someone'

        subject = 'saythanks.io: {} sent a note!'.format(who)
        message = TEMPLATE.format(note.body, note.byline, note_url, note_url2)
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
