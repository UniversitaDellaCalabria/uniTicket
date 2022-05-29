Production Setup
----------------

After the following actions being made, copy and adapt the production configurations that you found in `uwsgi_setup/` folder.

````
apt install python3-dev python3-pip libmagic-dev
pip3 install virtualenv
virtualenv -ppython3 uniticket.env
source uniticket.env/bin/activate
git clone https://github.com/UniversitaDellaCalabria/uniTicket.git uniticket
cd uniticket

# CONFIGURATION
# create your project settings
cat uni_ticket_project/settingslocal.py.example > uni_ticket_project/settingslocal.py

# edit settings ...
# set DEBUG=False

# create your MysqlDB
export USER='thatuser'
export PASS='thatpassword'
export HOST='%'
export DB='uniticket'

# tested on Debian 10
sudo mysql -u root -e "\
CREATE USER IF NOT EXISTS '${USER}'@'${HOST}' IDENTIFIED BY '${PASS}';\
CREATE DATABASE IF NOT EXISTS ${DB} CHARACTER SET = 'utf8' COLLATE = 'utf8_general_ci';\
GRANT ALL PRIVILEGES ON ${DB}.* TO '${USER}'@'${HOST}';"

# that's for saml2 (not mandatory, can even disable djangosaml2 in settings.INSTALLED_APPS)
cat saml2_sp/settings.py.example > saml2_sp/settings.py

# unical base template - modify templates/base-setup.html to customize your UI
curl https://raw.githubusercontent.com/italia/design-django-theme/master/bootstrap_italia_template/templates/bootstrap-italia-base.html --output templates/base-setup.html

# create generic certificates
pushd saml2_sp/saml2_config/certificates
openssl req -nodes -new -x509 -newkey rsa:2048  -days 3650 -keyout key.pem -out cert.pem
popd
# END CONFIGURATION

pip3 install -r requirements.txt
pip3 install uwsgi

sudo apt install mariadb-server libmariadbclient-dev
sudo apt install poppler-utils xmlsec1 gobject-introspection
sudo apt install supervisor

./manage.py migrate
./manage.py compilemessages
./manage.py collectstatic
./manage.py createsuperuser
./manage.py runserver

# if everything works, the big part is done!
````
