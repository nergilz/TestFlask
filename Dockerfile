FROM python:latest
RUN apt-get update
RUN apt-get dist-upgrade -y

RUN WEB=noninteractive apt-get -y dist-upgrade
RUN WEB=noninteractive apt-get -y install python-software-properties
RUN WEB=noninteractive apt-get -y install software-properties-common
RUN WEB=noninteractive apt-get install -y  tesseract-ocr
RUN WEB=noninteractive apt-get install -y libxss1 libappindicator1 libindicator7 xvfb wget
RUN WEB=noninteractive apt-get install -y fonts-liberation gconf-service libasound2 libgconf-2-4 libnspr4 libnss3 lsb-release xdg-utils libatk-bridge2.0-0 libgtk-3-0
RUN WEB=noninteractive wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN WEB=noninteractive dpkg -i google-chrome*.deb
RUN apt-get install -f -y

ADD . /opt/project
WORKDIR /opt/project
RUN pip install -r requirements.txt