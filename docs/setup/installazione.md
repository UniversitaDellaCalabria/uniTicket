# Installazione

### Requisiti

```
# Bash
sudo apt install xmlsec1 python3-dev python3-pip libssl-dev libsasl2-dev libldap2-dev
```

MariaDB
```
# Bash
sudo apt install mariadb-server libmariadbclient-dev libmariadb-dev-compat
```

PostreSQL
```
# Bash
sudo apt install postgresql postgresql-contrib libpq-dev
```

### Virtualenv

```
# Bash
pip3 install virtualenv
python3 -m venv uniticket.env
source uniticket.env/bin/activate
```

### Download del software e dipendenze

```
# Bash
git clone https://github.com/UniversitaDellaCalabria/uniTicket.git
cd uniTicket
pip3 install -r requirements.txt
```