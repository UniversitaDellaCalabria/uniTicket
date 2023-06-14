# DOCKER-VERSION 17.10.0-ce
FROM python:3-slim-bullseye
MAINTAINER Giuseppe De Marco <giuseppe.demarco@unical.it>
# thanks to Marco Spasiano to have moved things :)

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install dependencies
RUN pip install --upgrade pip

# install dependencies
RUN apt update \
    && apt install -y poppler-utils git locales xmlsec1 gcc \
                      libmagic-dev libmariadb-dev-compat libssl-dev \
                      libsasl2-dev libldap2-dev net-tools tcpdump \
                      curl iproute2 libgtk2.0-0 libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install virtualenv
RUN virtualenv -ppython3 helpdesk.env
RUN . helpdesk.env/bin/activate

# generate locales
RUN sed -i 's/# it_IT.UTF-8 UTF-8/it_IT.UTF-8 UTF-8/' /etc/locale.gen
RUN locale-gen it_IT.UTF-8
# set system-wide locale settings
ENV LANG it_IT.UTF-8
ENV LANGUAGE it_IT
ENV LC_ALL it_IT.UTF-8

COPY requirements.txt /
RUN pip3 install -r requirements.txt

# use bootstrap_italia as default template
# RUN ls ./templates
# RUN curl https://raw.githubusercontent.com/italia/design-django-theme/master/bootstrap_italia_template/templates/bootstrap-italia-base.html --output templates/base-setup.html
