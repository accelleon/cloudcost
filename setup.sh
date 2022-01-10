#!/bin/bash
# Bit of setup for the DB and python

# Grab required packages
sudo apt-get install postgresql python3 python3-pip unzip -y
# Update pip to latest version
python3 -m pip install pip -U
# Grab required python dependencies
python3 -m pip install install psycopg2-binary python-dateutil openpyxl ovh
# Generate our DB password
db_pass=$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${1:-32})
# Generate our config file
tee db.conf <<EOF 2>&1 > /dev/null
[database]
host = 127.0.0.1
port = 5432
password = $db_pass
user = cloudcost
database = cloudcost

[mattermost]
server = 
channel_id = 
token = 
EOF
# Create database user, and assign previleges
sudo -u postgres `psql -d postgres -c "create user cloudcost with createdb password '$db_pass';"`

sudo -u postgres `psql -d postgres -c "grant all privileges on database cloudcost to cloudcost;"`

sudo -u postgres `psql -d postgres -c "grant all privileges on all tables in schema public to cloudcost;"`

# Install AWS Cli
mkdir aws
cd aws
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install