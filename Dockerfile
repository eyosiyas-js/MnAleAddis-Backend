# base image
FROM python:3.9

# maintainer
LABEL Author="Yeabsira Ashenafi"

# The environemnet variable ensures that the python
# output to the terminal without buffering it first

ENV PYTHONUNBUFFERED 1

# switch to the app directory so that everything runs from here
WORKDIR /app 
COPY requirements.txt /app/requirements.txt

# installs the requirements
RUN pip install -r requirements.txt
RUN pip install django==3.0.5
RUN pip3 install pyOpenSSL --upgrade

COPY . /app

# command to run the project
CMD python manage.py runserver 0.0.0.0:17003