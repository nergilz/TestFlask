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

#Copy project and install packages
ADD . /project
WORKDIR /project
RUN pip install -r requirements.txt


