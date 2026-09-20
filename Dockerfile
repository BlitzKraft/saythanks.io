FROM python:3.10-slim

# Install system dependencies for psycopg2 and lxml
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /saythanks

# Upgrade pip first
RUN pip install --upgrade pip

# Install requirements with timeout and retry to handle slow networks
COPY ./requirements.txt .
RUN pip install --timeout=120 --retries=5 \
    appdirs "auth0-python<=2" blinker click colorama contextlib2 crayons dateparser \
    docopt flake8 "flask<2.3" flask-qrcode gunicorn humanize itsdangerous jinja2 \
    lxml_html_clean markupsafe maya names ordereddict packaging pendulum psycopg2 \
    pyjwt pyment pytest pyparsing pytest-cov python-dateutil python-http-client \
    pytz pytzdata raven regex requests "ruamel.yaml" "mailersend==0.6.0" six \
    "sqlalchemy<2.0.0" tablib tzlocal werkzeug whitenoise python-dotenv markdown

# Copy the app
COPY . .

EXPOSE 5000

# Run gunicorn as per Procfile
CMD ["gunicorn", "saythanks:app", "-w", "2", "--bind", "0.0.0.0:5000", "--log-file", "-"]
