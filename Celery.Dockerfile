FROM python:latest
RUN apt-get update
RUN apt-get dist-upgrade -y

#Update Packages
RUN WEB=noninteractive apt-get -y dist-upgrade
RUN WEB=noninteractive apt-get -y install python-software-properties
RUN WEB=noninteractive apt-get -y install software-properties-common

#Install Tesseract-OCR and dependences
RUN WEB=noninteractive apt-get install -y  tesseract-ocr
RUN WEB=noninteractive apt-get install -y libxss1 libappindicator1 libindicator7 xvfb wget

#Install Chrome with dependences
RUN WEB=noninteractive apt-get install -y fonts-liberation gconf-service libasound2 libgconf-2-4 libnspr4 libnss3 lsb-release xdg-utils libatk-bridge2.0-0 libgtk-3-0
RUN WEB=noninteractive wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN WEB=noninteractive dpkg -i google-chrome*.deb
RUN apt-get install -f -y

#Copy project and install packages
ADD . /project
WORKDIR /project
RUN pip install -r requirements.txt

#Create Celery user
RUN adduser -D -u 1000 celery

