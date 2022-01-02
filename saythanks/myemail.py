import os

import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail
from . import exceptions
from urllib.error import URLError
# from python_http_client.exceptions import HTTPError
# import http.client

# Email Infrastructure
# --------------------

API_KEY = os.environ['SENDGRID_API_KEY']
sg = sendgrid.SendGridAPIClient(api_key=API_KEY)

TEMPLATE = """{}

--{}

=========

This note of thanks was brought to you by SayThanks.io.

A KennethReitz project, now maintained by KGiSL Edu (info@kgisl.com).
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
        message = TEMPLATE.format(note.body, note.byline)

        from_address = Email('no-reply@saythanks.io', name="SayThanks.io")
        to_address = Email(email_address)
        content = Content('text/plain', message)

        mail = Mail(from_address, subject, to_address, content)
        response = sg.client.mail.send.post(request_body=mail.get())

    except exceptions.HTTPError as e:
        print(e.to_dict)
    except URLError as e:
        print(e)

    # Other options that were ineffective
    #
    # except http.client.HTTPException as e:
    #    print(e.to_dict)
    # except Exception as e:
    #    print(e)
