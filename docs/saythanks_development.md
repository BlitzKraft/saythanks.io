**Development Environment Setup Guide for Windows OS**

1. Go to run (Windows + R) and type **appwiz.cpl**

   > ![C:\Users\dinesh.p\Pictures\My Screen Shots\Screen Shot 04-16-21 at 12.39 PM.PNG](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.001.png)

2. Click Turn windows features on or off in the left hand side menu

3. Check “Windows subsystem for Linux” and click OK. After the successful installation restart your PC.

   > ![C:\Users\dinesh.p\Pictures\My Screen Shots\Screen Shot 04-16-21 at 12.39 PM 001.PNG](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.002.png)

4. Go to windows store and search for **Ubuntu 18** and install

   > ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.003.jpeg)

5. During first run on Ubuntu, configure the user name and password

- Execute below commands:
  - **sudo apt update**
  - **sudo apt install libpq-dev python3-dev**
  - **sudo apt install python3-pip**

6. Get the repository by using below command:

   git clone [https://github.com/BlitzKraft/saythanks.io.git](https://github.com/BlitzKraft/saythanks.io.git)

7. Go inside the saythanks.io folder (**cd saythanks.io)** and install the required packages by using below command:
   ` `**pip3 install -r requirements.txt**

   Note: If any error is faced in requirements.txt installation, Run the below command:

   python3 -m pip install --upgrade pip
   python3 -m pip install --upgrade pillow

8. Go to Auth0 login website - https://auth0.com/docs/login

> ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.004.png)

9.  ` `Click Applications in the left hand side menu - > Applications - > Create Application - > Regular Web Applications -> Create

    > ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.005.png)

10. Open “Saythanks” application (Regular web applications) to get the below keys:

    > ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.006.png)

11. And add Call back URL as below (in the same page) and click “**Save**”:

> ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.007.png)

12. Click APIs in Applications (Refer below image )and Create API

    > ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.008.png)

13. Click Auth0 Management API - > API Explorer - > Copy Token (AUTH0_JWT_V2_TOKEN)
     
     ![image](https://user-images.githubusercontent.com/63831132/149557084-3da38b01-97ad-4fba-aa71-9c8a91bf1454.png)


14. \*\* Go to <https://app.sendgrid.com>

15. ` `Create and get API Key as mentioned below:

> ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.009.jpeg)

16. Add environmental variables values related to project on .bashrc file (file located on /home/[user]/.bashrc) as below:

    export DATABASE_URL="postgresql://user:pwd@server_ip/database_name"
    export SENDGRID_API_KEY=''
    export AUTH0_CLIENT_ID=''
    export AUTH0_CLIENT_SECRET=
    export AUTH0_CALLBACK_URL='http://localhost:5000/callback'
    export AUTH0_DOMAIN=''
    export AUTH0_JWT_V2_TOKEN=''

17. Go to “<https://www.enterprisedb.com/downloads/postgres-postgresql-downloads>” , download and install the required version of “Postgres”

18. Go inside “postgres” installation path
19. Configure password and create database in “Postgres” (Refer below image):

    > ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.010.jpeg)

20. Download the schema.sql file from the link : “<https://github.com/BlitzKraft/saythanks.io/tree/master/saythanks/sqls>” and paste it in required local drive

21. To Configure development environment in Visual Source Code:

- Go to powershell - > and then Type
- > **wsl**
- Go to saythanks folder (Refer below image) -> and then Type
- > `code .`

  > ![](Aspose.Words.a8e7dec5-037d-4b33-9c46-a86e9c3e100a.011.jpeg)

- It will automatically open the project in Visual Source Code (VSC)

### Congratulations for having setup your own local development environment for saythanks.io!

- Godspeed!






**Steps to resolve AUTH0 expiry:**

1.	Go to Auth0 login website - https://auth0.com/docs/login

  ![image](https://user-images.githubusercontent.com/63831132/149557335-1856e60c-cede-449a-bc97-8b3763728909.png)



2.	Click Applications in the left hand side menu - > Applications


3.	Click “API Explorer Application”
  
  ![image](https://user-images.githubusercontent.com/63831132/149557423-79bf9a7e-cac8-44c9-8a10-6eadb7de872d.png)

     

4.	Go to APIs tab and Click “Auth0 Management API”

   ![image](https://user-images.githubusercontent.com/63831132/149557472-f50a5b5a-f6f4-47cb-9af5-a297b9ca07e3.png)



5.	Go to API Explorer tab and Copy the token (as mentioned in below image):

   ![image](https://user-images.githubusercontent.com/63831132/149557543-654194f3-1b4c-4099-a0bc-8110332fbec2.png)



6.	Paste the token in .bashrc file and save it
 
    ![image](https://user-images.githubusercontent.com/63831132/149557575-26436aea-cdac-4bc2-b8ba-f8ee99d1b22a.png)

	
7.	Run the command “source ~/.bashrc”
8.	If virtual environment is used, activate it using the command “source YOUR_VIRTUAL_ENV_NAME/bin/activate”
9.	Re-run the saythanks.io application
