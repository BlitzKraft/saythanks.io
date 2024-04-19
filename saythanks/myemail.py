import os

import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail,To
from urllib.error import URLError

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
=========
<br>
<br>
This note of thanks was brought to you by SayThanks.io.
<br>
<br>
A KennethReitz project, now maintained by KGiSL Edu (info@kgisl.com).
</div>
"""


def notify(note, email_address):
    """Use the note contents and a template, build a
    formatted message. Use sendgrid to deliver the formatted
    message as an email to the user.
    """
    try:
        # Say 'someone' if the byline is empty.
        who = note.byline or 'someone'

        subject = 'saythanks.io: {} sent a note!'.format(who)
        message = note.body
        message = TEMPLATE.format(note.body, note.byline)
        from_address = Email('no-reply@saythanks.io', name="SayThanks.io")
        to_address = To(email_address)
        content = Content('text/html', message)
        mail = Mail(from_address,to_address,subject,content)
        sg.client.mail.send.post(request_body=mail.get())
    except URLError as e:
        logging.error("URL Error occured "+str(e))
        print(e)
    # except Exception as e:
    #    print(e)
