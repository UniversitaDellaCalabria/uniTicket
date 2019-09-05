uniTicket
---------

Is a support Software that let us manage tickets and generic submission modules with our user.
Featurset:

- Multi Tenant. Multiple office and organizational areas support in a single, unified, system;
- Possibility to transfer and share tickets between different office/areas;
- Multi role, multiple ticket ownership;
- Possibility to add data consent or agreement submission before a ticket being created;
- ticket interdependencies;
- todo list for every ticket, to follow user to do things before submission;
- Custom fields, custom complex field, custom multi row (table) fields with configurable fancy widgets;
- Pdf and p7m signed fields, with validation on data integrity (attachment);
- Report summary via email about pending tickets to office's operators;
- datatables ajax server side processing, very good performances on mobile device;
- Responsive template for a better mobile experience;
- SAML2 SSO integration (pySAML2);
- Fully compliant Agid visual guidelines.


Gallery
-------

[screen shots here]


Requirements
------------

````
 sudo apt install xmlsec1 mariadb-server libmariadbclient-dev python3-dev python3-pip libssl-dev libmariadb-dev-compat libsasl2-dev libldap2-dev

 pip3 install virtualenv
 virtualenv -ppython3 helpdesk.env
 source helpdesk.env/bin/activate
````

Database setup
--------------

````
export USER='username del db in settingslocal.py'
export PASS='la password configurata in settingslocal.py'
export HOST='host del db in settingslocal.py'
export DB='db name in settingslocal.py'

mysql -u root -e "\
CREATE USER IF NOT EXISTS ${USER}@'${HOST}' IDENTIFIED BY '${PASS}';\
CREATE DATABASE ${DB} CHARACTER SET utf8 COLLATE utf8_general_ci;\
GRANT ALL PRIVILEGES ON ${DB}.* TO ${USER}@'${HOST}';"
````

Import Example configuration
----------------------------

````
./manage.py loaddata examples/unical_accounts.json
./manage.py loaddata examples/organizational_area.json
./manage.py loaddata examples/uni_ticket.json
````


Todo
----

- Advanced search (with AND, OR)
