import os

import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail

# Email Infrastructure
# --------------------

API_KEY = os.environ['SENDGRID_API_KEY']
sg = sendgrid.SendGridAPIClient(apikey=API_KEY)

TEMPLATE = """{}

--{}

=========

This note of thanks was brought to you by SayThanks.io.

A Kenneth Reitz (me@kennethreitz.org) project.
"""


def notify(note, email_address):
    """

    :param note: 
    :param email_address: 

    """

    # Say 'someone' if the byline is empty.
    who = note.byline or 'someone'

    subject = 'saythanks.io: {} sent a note!'.format(who)
    message = TEMPLATE.format(note.body, note.byline)

    from_address = Email('no-reply@saythanks.io', name="SayThanks.io")
    to_address = Email(email_address)
    content = Content('text/plain', message)

    mail = Mail(from_address, subject, to_address, content)
    response = sg.client.mail.send.post(request_body=mail.get())
