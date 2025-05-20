from dotenv import load_dotenv
import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, Content
from urllib.error import URLError
import logging

# Load environment variables from .env (for local testing)
load_dotenv()

# Create and configure logger
logging.basicConfig(
    filename='Logfile.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
logger = logging.getLogger()

# Email Infrastructure
API_KEY = os.getenv('SENDGRID_API_KEY')
if not API_KEY:
    raise RuntimeError("SENDGRID_API_KEY not set. Please add it to your environment or .env file.")

sg = sendgrid.SendGridAPIClient(api_key=API_KEY)

# Email template including public URL placeholder
TEMPLATE = """<div>
{body}
<br><br>
<a href="{public_url}">Read your thank‑you note here</a>
<br><br>
-- {byline}
<br><br>
=========
<br><br>
This note of thanks was brought to you by SayThanks.io.
<br><br>
A KennethReitz project, now maintained by KGiSL Edu (<a href="mailto:info@kgisl.com">info@kgisl.com</a>).
</div>
"""

def notify(note, email_address, base_url="https://saythanks.io"):
    """
    Sends a thank‑you email via SendGrid, including a public URL to view the note online.
    """
    try:
        who = note.byline or 'someone'
        subject = f"saythanks.io: {who} sent a note!"
        public_url = f"{base_url}/note/{note.uuid}"

        html_body = TEMPLATE.format(
            body=note.body,
            byline=note.byline,
            public_url=public_url
        )
        text_body = (
            f"{note.body}\n\n"
            f"Read your thank‑you note here: {public_url}\n\n"
            f"-- {who}"
        )


        mail = Mail(
            from_email=('no‑reply@saythanks.io', 'SayThanks.io'),
            to_emails=email_address,
            subject=subject,
            plain_text_content=text_body,
            html_content=html_body
        )

        response = sg.send(mail)
        status = response.status_code
        print("Success 200" if status < 300 else f"Failed with status: {status}")
        logger.info(f"Email send attempt to {email_address} returned status {status}")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        print(f"Error: {e}")
