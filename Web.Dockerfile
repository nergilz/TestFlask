FROM python:latest

#Copy project and install packages
ADD . /project
WORKDIR /project
RUN pip install -r requirements.txt