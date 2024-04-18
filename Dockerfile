FROM ubuntu:22.04

# Installing python
RUN apt-get update
RUN apt-get install -y libpq-dev 
RUN apt-get install -y python3-dev 
RUN apt-get install -y python3-pip 
RUN apt-get clean

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade pillow

WORKDIR /saythanks

# Installing requirements
COPY ./requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Copying the app
COPY . .

EXPOSE 5000
CMD [ "python3", "t.py" ]
