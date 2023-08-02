# wireflaskadmin
## Project description
Minimal wireguard configuration /management webapp.

The project is split into two parts(possibly three), the webapp and the daemon(and possibly an api agent)

The webapp should run as a normal user, since it's not a good idea to run an internet facing application as root, however the daemon is the part that manage wireguard configs, and the wg-quick services and it should run as root(because the daemon needs the privileges to read and write to /etc/wireguard and execute systemctl commands to manage the services).
## Project status
It's in early development stage, the webapp is pretty much done, lacking only the API, some UI/UX refinements, and also some extensive testing, and the daemon is implemented but need to be properly tested and possibly some work on exception handling.
Feel free to contribute to the project, either with python code, unit tests, or html/css/js or even translating or improving this readme file, or even documentation.
## Features
### Endpoint Management
Have entries for each endpoint(wireguard interface) that you host, private keys and pubkeys are created by the daemon with its own interface config, and only the pubkey is available for the webapp for security reasons.
### Peer Management
Each peer is linked to an endpoint, and you can manage each one of them, and once you tell the daemon to rebuild the configuration it will rebuild and restart the interface(s).
### Authentication
The authentication to change the configurations are provided by PAM, if someone wants to add support to LDAP please feel free to contribute.
## Planned Features
- Web API that returns a wireguard "Endpoint" or "Peer" configuration.
- API Agent that poll the Web API and automatically deploy the provisioned configuration.
- reCaptcha(or some other captcha system) on login to make bruteforcing a bit more difficult.
- 2FA for that extra bit of security.
## Installation
- **Observation**: This document doesn't cover the install and setup of wireguard or configuring forwarding/nat and other firewall rules!
### Prerequisites
- Python 3.11
- python-venv
- python-pip
- Maria DB
### Setting up the default language for the webapp
Make a symlink on webapp/wfadmin/translations of your intended language(for example en_us.py) to default.py (ln -s en_us.py default.py)
### Installing MariaDB
- Using your distro package manager install MariaDB Server( on debian/ubuntu should be `apt install mariadb-server`)
- Enable MariaDB server with `systemctl enable mariadb.service`
- Start MariaDB server with `systemctl start mariadb.service`
### Setting up Maria DB
This example will create a database called wfadmin, that will be accessed by the user wfadmin with a password abcd1234, please change that on production!
- CREATE DATABASE wfadmin;
- CREATE USER 'wfadmin'@'localhost' IDENTIFIED BY 'abcd1234';
- GRANT ALL PRIVILEGES ON wfadmin.* TO 'wfadmin'@'localhost';
- FLUSH PRIVILEGES
### Understanding the configuration
- **WFADMIN_SECRET_KEY** is used as a secret key to sign stuff on the application, usually cookies, please don't reuse!
- **WFADMIN_RECAPTCHA_API_KEY** is your recaptcha API key that will be implemented on login(raises the bar for bruteforce attacks)
- **WFADMIN_RECAPTCHA_SITE_KEY** is your recaptcha SITE key that will be implemented on login(raises the bar for bruteforce attacks)
- **WFADMIN_SQLALCHEMY_DATABASE_URI** is the URI for the database, its composed by:
- -Protocol(default: mysql+pymysql://)
- -Username:Password@host:port/databasename
- **WFADMIN_ENDPOINT_AUTOIP** is for getting your WAN IP address to autofill when creating a new endpoint.
- **WFADMIN_REBUILD_STARTUP** is for automatically rebuilding all configurations and restarting all the interfaces.
### Making the .env file to configure the applications
- Create a file called .env on webapp/ with the following content
```
    WFADMIN_SECRET_KEY='INSERT YOUR SECRET KEY'
    WFADMIN_RECAPTCHA_API_KEY='INSERT YOUR RECAPTCHA API KEY'
    WFADMIN_RECAPTCHA_SITE_KEY='INSERT YOUR RECAPTCHA SITE KEY'
    WFADMIN_SQLALCHEMY_DATABASE_URI='mysql+pymysql://wfadmin:abcd1234@localhost:3306/wfadmin'
    WFADMIN_ENDPOINT_AUTOIP=N
    WFADMIN_REBUILD_STARTUP=N
```
Pro Tip: You can also make a symlink of it for the daemon/ directory
### Installing the webapp venv
- Change directory to the **webapp/** and execute `python -m venv .venv``
- Active your venv with source `.venv/bin/activate`
- Install the dependencies with `pip install -r requirements.txt`
- Install gunicorn(or whatever wsgi you want to use) with `pip install gunicorn`
### Installing the daemon venv
- Change directory to the **daemon/** and execute `python -m venv .venv``
- Active your venv with source `.venv/bin/activate`
- Install the dependencies with `pip install -r requirements.txt`
### Creating a systemd unit to automatically start the daemon
```
    [Unit]
    Description=WireFlaskAdmin Daemon
    After=mariadb.service
    Requires=mariadb.service
    [Service]
    WorkingDirectory=/path/to/wireflaskadmin/daemon
    User=root
    ExecStart=/path/to/wireflaskadmin/daemon/.venv/bin/python3 main.py
    Restart=always
    RestartSec=10
    [Install]
    WantedBy=multi-user.target
```
-Save it on `/etc/systemd/system/wgflaskd.service`
Note that you need to adjust the path to your needs both on **WorkingDirectory** and **ExecStart**
### Creating a systemd unit to automatically start the webapp
```
    [Unit]
    Description=WireFlaskAdmin WebApp
    After=mariadb.service
    Requires=mariadb.service
    [Service]
    WorkingDirectory=/path/to/wireflaskadmin/webapp
    User=youruser
    ExecStart=/path/to/wireflaskadmin/webapp/.venv/bin/gunicorn -w 3 app:app
    Restart=always
    RestartSec=10
    [Install]
    WantedBy=multi-user.target
```
-Save it on `/etc/systemd/system/wfadmin.service``
Note that you need to replace the **User** with the user intended to run the webapp(please don't use root), also adjust the **WorkingDirectory** and **ExecStart**
### Reloading systemd daemon
It is needed so systemd will see our new units so we can enable them and start them
- So execute as root(or using sudo) `systemctl daemon-reload`
### Enabling and starting our units
- Execute as root(or using sudo) `systemctl enable wgflaskd.service`
- Execute as root(or using sudo) `systemctl enable wfadmin.service`
- Execute as root(or using sudo) `systemctl start wgflaskd.service`
- Execute as root(or using sudo) `systemctl start wfadmin.service`
If everything is correct both the daemon and the webapp should be up and running.
**IMPORTANT NOTE:** Please don't let gunicorn face the internet directly, use like nginx reverse proxy or apache reverse proxy and configure SSL(letsencrypt certbot makes it really easy)
## Initial database setup
Right after installing and having the applications up and running, we will need to create the tables of the database, luckily SQLAlchemy will handle that for us.
- Using wget or curl visit http://localhost:8000/install
**Security advice**: if you configured a reverse proxy, make sure to redirect on nginx or apache the location /install to /, the software should prevent a new database setup, but let's play safe alright?

## Configuring your development environment(Linux)
### Webapp
- cd to webapp/
- On webapp/ create a .venv with python3 -m venv .venv
- activate your .venv with source .venv/bin/activate
- install the dependencies with pip using pip install -r requirements.txt
- Configure your favorite editor to use the python symlink in the webapp/.venv/ as the interpreter

### Daemon
- cd to daemon/
- On daemon/ create a .venv with python3 -m venv .venv
- activate your .venv with source .venv/bin/activate
- install the dependencies with pip using pip install -r requirements.txt
- Configure your favorite editor to use the python symlink in the daemon/.venv/ as the interpreter

## Thanks
Special thanks for rahlskog,mingalsuo and Theros from linux.chat Discord server
