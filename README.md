# wireflaskadmin
## Project description
Minimal wireguard configuration /management webapp.

The project is split into two parts, the webapp and the daemon; the webapp should run as a normal user, since it's not a good idea to run it as root; however the daemon is the part that manage wireguard configs, and the wg-quick services and it should run a root.
## Project status
It's in early development stage, the webapp is pretty much done but not tested, and the daemon still need to be implemented and tested.
Feel free to contribute to the project, either with python code, unit tests, or html/css/js or even translating or improving this readme file, or even documentation
## Features
### Endpoint Management
Have entries for each endpoint(wireguard interface) that you host, private keys and pubkeys are created by the daemon with its own interface config
### Peer Management
Each peer is linked to a endpoint, and you can manage each one of them, and once you tell the daemon to rebuild the configuration it will rebuild and restart the interface for you.
### Authentication
The authentication to change the configurations are provided by PAM, if someone wants to add support to LDAP please feel free to contribute.
## Thanks
Special thanks for rahlskog,mingalsuo and Theros from linux.chat Discord server

## Installation
### Prerequisites
- Python 3.11
- python-venv
- python-pip
- Maria DB
### Setting up the default language
Make a symlink on webapp/wfadmin/translations of your intended language(for example en_us.py) to default.py (ln -s en_us.py default.py)
### Setting up Maria DB
This example will create a database called wfadmin, that will be accessed by the user wfadmin with a password abcd1234, please change that on production!
- CREATE DATABASE wfadmin;
- CREATE USER 'wfadmin'@'localhost' IDENTIFIED BY 'abcd1234';
- GRANT ALL PRIVILEGES ON wfadmin.* TO 'wfadmin'@'localhost';
- FLUSH PRIVILEGES
### Making the .env file
- Create a file called .env on webapp/ with the following content

WFADMIN_SECRET_KEY='INSERT YOUR SECRET KEY'
WFADMIN_RECAPTCHA_API_KEY='INSERT YOUR RECAPTCHA API KEY'
WFADMIN_RECAPTCHA_SITE_KEY='INSERT YOUR RECAPTCHA SITE KEY'
WFADMIN_SQLALCHEMY_DATABASE_URI='mysql+pymysql://wfadmin:abcd1234@localhost:3306/wfadmin'
WFADMIN_ENDPOINT_AUTOIP=N
### Understanding the configuration
- WFADMIN_SECRET_KEY is used as a secret key to sign stuff on the application, usually cookies, please don't reuse!
- WFADMIN_RECAPTCHA_API_KEY is your recaptcha API key that will be implemented on login(raises the bar for bruteforce attacks)
- WFADMIN_RECAPTCHA_SITE_KEY is your recaptcha SITE key that will be implemented on login(raises the bar for bruteforce attacks)
- WFADMIN_SQLALCHEMY_DATABASE_URI is the URI for the database, its composed by:
- -Protocol(default: mysql+pymysql://)
- -Username:Password@host:port/databasename
- WFADMIN_ENDPOINT_AUTOIP is for getting your WAN IP address to autofill when creating a new endpoint
## Configuring your development environment(Linux)
### Webapp
- cd to webapp
- On webapp/ create a .venv with python3 -m venv .venv
- activate your .venv with source .venv/bin/activate
- install the dependencies with pip using pip install -r requirements.txt
- Configure your favorite editor to use the python symlink in the webapp/.venv/ as the interpreter
###