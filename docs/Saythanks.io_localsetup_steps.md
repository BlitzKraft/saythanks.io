**Saythanks.io Local Setup User Manual**

**Step 1:**

To Use Ubuntu in windows

Go to run and type **appwiz.cpl**

![C:\Users\dinesh.p\Pictures\My Screen Shots\Screen Shot 04-16-21 at 12.39 PM.PNG](Aspose.Words.088e8827-271b-49be-a857-24af23d20c3f.001.png)

**Step 2:**

Open Turn windows features on or off

![C:\Users\dinesh.p\Pictures\My Screen Shots\Screen Shot 04-16-21 at 12.39 PM 001.PNG](Aspose.Words.088e8827-271b-49be-a857-24af23d20c3f.002.png)

Select Windows subsystem for linux and click ok, once feature is installed restart your PC

**Step 3:**

Go to windows store and search for **Ubuntu 18** and install

**Step 4:**

ON Ubuntu for Windows

During first run on UBUNTU give user name and password

**Step 5:**

On Ubuntu terminal:

Execute below commands:

**sudo apt update**

**sudo apt install libpq-dev python3-dev**

**sudo apt install python3-pip**

**Step 6:**

Download the source code from git repository

` `(or)

Get the repository by using git clone

git clone <https://github.com/BlitzKraft/saythanks.io.git>

**Step 7:**

In command prompt, go inside the saythanks.io folder and install the required pacakages by using below command

**pip3 install -r requirements.txt**

**Step 8:**

To run the project, you need to set the following environment variables:

\- SENDGRID_API_KEY

\- DATABASE_URL

\- SENTRY_DSN

\- AUTH0_DOMAIN

\- AUTH0_JWT_TOKEN

\- AUTH0_CLIENT_ID

\- AUTH0_CLIENT_SECRET

\- AUTH0_CALLBACK_URL

**Add environmental variables values related to project on .bashrc file (file located on /home/[user]/.bashrc)**

export DATABASE_URL="postgresql://user:password@server_ip/database_name"

export SENDGRID_API_KEY=''

export AUTH0_CLIENT_ID=''

export AUTH0_CLIENT_SECRET=''

export AUTH0_CALLBACK_URL=''

export AUTH0_DOMAIN=''

export AUTH0_JWT_TOKEN=''

export AUTH0_JWT_V2_TOKEN=''

save and run the command **source /home/[user]/.bashrc** in terminal

**(You need to sign up with auth0 and sendgrid website to get keys)**

**Step 9:**

Set your local system IP for running the application.

Open the t.py file from corresponding source code folder and give your local system IP and port.

![](Aspose.Words.088e8827-271b-49be-a857-24af23d20c3f.003.png)

**Step 10:**

Once done. Run the t.py file. You will get the link in server log.

![](Aspose.Words.088e8827-271b-49be-a857-24af23d20c3f.004.png)

**Step 11:**

Access the application using the link received from server log.

![](Aspose.Words.088e8827-271b-49be-a857-24af23d20c3f.005.png)

**Step 12:**

If you need to change the source code for the project.

You can go to the source code path and you can edit by using editor like Geany or PyCharm

or

You can directly edit using vi or nano command

vi t.py or nano t.py

**Below are the list of packages to be installed with respective versions (FYR):**

appdirs==1.4.3

auth0-python==2.0.1

blinker==1.4

click==6.7

colorama==0.3.9

contextlib2==0.5.5

crayons==0.1.2

dateparser==0.6.0

docopt==0.6.2

Flask==0.12.1

Flask-Cache==0.13.1

Flask-Common==0.1.0

gunicorn==19.7.1

humanize==0.5.1

itsdangerous==0.24

Jinja2==2.9.6

MarkupSafe==1.0

maya==0.1.8

names==0.3.0

packaging==16.8

pendulum==1.2.0

psycopg2==2.7.1

PyJWT==1.5.0

pyparsing==2.2.0

python-dateutil==2.6.0

python-http-client==2.2.1

pytz==2017.2

pytzdata==2017.2

raven==6.0.0

records==0.5.0

regex==2017.4.29

requests==2.13.0

ruamel.ordereddict==0.4.9

ruamel.yaml==0.14.11

sendgrid==4.0.0

six==1.10.0

SQLAlchemy==1.1.9

tablib==0.11.4

tzlocal==1.4

Werkzeug==0.12.1

whitenoise==3.3.0
