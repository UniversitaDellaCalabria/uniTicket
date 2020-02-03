# DOCKER-VERSION 17.10.0-ce
FROM python:slim
MAINTAINER Giuseppe De Marco <giuseppe.demarco@unical.it>

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install dependencies
RUN pip install --upgrade pip

# install dependencies
RUN apt-get update \
    && apt-get install -y poppler-utils git locales xmlsec1 gcc \
                          libmagic-dev libmariadbclient-dev libssl-dev \
                          libsasl2-dev libldap2-dev net-tools tcpdump \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install virtualenv
RUN virtualenv -ppython3 helpdesk.env
RUN . helpdesk.env/bin/activate

# generate chosen locale
RUN sed -i 's/# it_IT.UTF-8 UTF-8/it_IT.UTF-8 UTF-8/' /etc/locale.gen
RUN locale-gen it_IT.UTF-8
# set system-wide locale settings
ENV LANG it_IT.UTF-8
ENV LANGUAGE it_IT
ENV LC_ALL it_IT.UTF-8

COPY . /uniTicket
WORKDIR /uniTicket
RUN pip3 install -r requirements.txt
RUN cp uni_ticket_project/settingslocal.py.example uni_ticket_project/settingslocal.py

## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.2/wait /wait
RUN chmod +x /wait

RUN python manage.py migrate
# ADMIN as USERNAME, ADMINPASS as PASSWORD
RUN python manage.py shell -c "from django.contrib.auth import get_user_model; get_user_model().objects.filter(username='admin').exists() or get_user_model().objects.create_superuser('admin', 'admin@example.com', 'adminpass')"
EXPOSE 8000
CMD /wait && python manage.py runserver 0.0.0.0:8000
