# Installazione

## Requisiti

```
sudo apt install xmlsec1 mariadb-server libmariadbclient-dev python3-dev python3-pip libssl-dev libmariadb-dev-compat libsasl2-dev libldap2-dev

pip3 install virtualenv
python3 -m venv uniticket.env
source uniticket.env/bin/activate

## Download del software e dipendenze

git clone https://github.com/UniversitaDellaCalabria/uniTicket.git
cd uniTicket
pip3 install -r requirements.txt
```

Convert HTML to PDF using Webkit (QtWebKit)

```
wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.buster_amd64.deb
sudo dpkg -i wkhtmltox_0.12.5-1.buster_amd64.deb
sudo apt install -f
```