FROM ubuntu:trusty
RUN apt-get update
RUN apt-get dist-upgrade -y

RUN WEB=noninteractive apt-get -y dist-upgrade
RUN WEB=noninteractive apt-get -y install python-software-properties
RUN WEB=noninteractive apt-get -y install software-properties-common
RUN WEB=noninteractive add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN WEB=noninteracitve apt-get autoremove -y python3 python3.4
RUN WEB=noninteractive apt-get install -y python3.5 python3.5-dev libjpeg-dev libtiff-dev
RUN WEB=noninteractive apt-get install -y  tesseract-ocr
RUN WEB=noninteractive apt-get install -y libxss1 libappindicator1 libindicator7 xvfb wget
RUN WEB=noninteractive apt-get install -y fonts-liberation gconf-service libasound2 libgconf-2-4 libnspr4 libnss3 lsb-release xdg-utils
RUN WEB=noninteractive wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN WEB=noninteractive dpkg -i google-chrome*.deb
RUN apt-get install -f -y

ADD . /code
WORKDIR /code