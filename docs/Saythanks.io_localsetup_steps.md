**Saythanks.io Local Setup User Manual**

1. Go to run (Windows + R) and type **appwiz.cpl**

![C:\Users\dinesh.p\Pictures\My Screen Shots\Screen Shot 04-16-21 at 12.39 PM.PNG](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.001.png)

1. Click Turn windows features on or off in the left hand side menu
1. Check “Windows subsystem for Linux” and click ok, After the successful installation restart your PC

![C:\Users\dinesh.p\Pictures\My Screen Shots\Screen Shot 04-16-21 at 12.39 PM 001.PNG](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.002.png)

1. Go to windows store and search for **Ubuntu 18** and install

![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.003.jpeg)

1. During first run on Ubuntu, configure the user name and password
1. Execute below commands:

- **sudo apt update**
- **sudo apt install libpq-dev python3-dev**
- **sudo apt install python3-pip**

1. Get the repository by using below command:

` `**git clone [https://github.com/BlitzKraft/saythanks.io.git**](https://github.com/BlitzKraft/saythanks.io.git)\*\*

1. Go inside the saythanks.io folder (**cd saythanks.io)** and install the required packages by using below command:

` `**pip3 install -r requirements.txt**

1. Go to Auth0 login website - https://auth0.com/docs/login

![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.004.png)

1. ` `Click Applications in the left hand side menu - > Applications - > Create Application - > Regular Web Applications -> Create

\*\*

` `**![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.005.png)**

1. Open “Saythanks” application (Regular web applications) to get the below keys:
   \*\*

` `**![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.006.png)**

1. And add Call back URL as below (in the same page) and click “**Save**”:

` `**![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.007.png)**

1. Click APIs in Applications (Refer below image )and Create API

` `**![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.008.png)**

1. Click Auth0 Management API - > API Explorer - > Copy Token

1. \*\* Go to <https://app.sendgrid.com>

1. ` `Create and get API Key as mentioned below:

` `**![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.009.jpeg)**

1. Add environmental variables values related to project on .bashrc file (file located on /home/[user]/.bashrc) as below:

export DATABASE_URL="postgresql://user:pwd@server_ip/database_name"

export SENDGRID_API_KEY=''

export AUTH0_CLIENT_ID=''

export AUTH0_CLIENT_SECRET=

export AUTH0_CALLBACK_URL='http://localhost:5000/callback'

export AUTH0_DOMAIN=''

export AUTH0_JWT_V2_TOKEN=''

1. Go to “<https://www.enterprisedb.com/downloads/postgres-postgresql-downloads>” , download and install the required version of “Postgres”

1. Go inside “Postgres” installation path

1. Configure password and create database in “Postgres” (Refer below image):

` `**![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.010.jpeg)**

1. Download the schema.sql file from the link : “<https://github.com/BlitzKraft/saythanks.io/tree/master/saythanks/sqls>” and paste it in required local drive

1. To Configure development environment in Visual Source Code:

- **Go to powershell - > Type wsl**
- **Go to saythanks folder (Refer below image) -> Type “code .” – It will automatically open the project in visual studio code**

` `**![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.011.jpeg)**
