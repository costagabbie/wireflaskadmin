# Installing WireFlaskAdmin
## Deciding what to use
Well some administrators will want to have the wireflaskadmin daemon to do the 'dirty work' of managing the services and writing configuration files, some others may not.
In the case the web application still can be used, however the rebuild/start/stop/restart options will not work, however you can still have the configuration files generated using the web API, in that case you can use your shell script with curl or wget and do your magic to do the management, in some scenarios it might also be the only option.
## Dependencies
### Common dependencies
- Maria DB SQL Server
- nginx or apache or whatever reverse proxy capable webserver you want (nginx recommended).
- Python 3
- Python 3 venv
- Python 3 pip
#### Installing the common dependencies on Debian
`# apt update && apt install mariadb-server nginx python3-venv python3-pip`
#### Installing the common dependencies on Gentoo
`# emerge -av dev-lang/python dev-python/pip dev-db/mariadb www-servers/nginx`
#### Installing the common dependencies on Fedora(should be the same on RHEL)
`# dnf install mariadb-server, nginx`
#### Installing the common depencies on Arch Linux
`# pacman -S mariadb-git nginx`
You should look your distro repository for those on debian they are, and probably you already have the python stuff installed.
### Dependencies for the webapp
They are listed as pip packages, and the project is developed with these versions in mind, however if you have these packages on your
distro repository, i guess you could try using those too
either way they are listed on requirements.txt on the webapp directory.
### Dependencies for the daemon
Same as above, however it uses the requirements.txt on the daemon directory.
## Creating the users
We recommend you to run the webapp under a regular user, as example we will use an user named `wireflask`
## Configuring the database
After installing MariaDB Server, enter mariadb shell as root and execute the following commands, replacing user and password, and database name as needed.
In the example the database name is wfadmin and the user is wfadmin with the password abcd1234
```
CREATE DATABASE wfadmin;
CREATE USER 'wfadmin'@'localhost' IDENTIFIED BY 'abcd1234';
GRANT ALL PRIVILEGES ON wfadmin.* TO 'wfadmin'@'localhost';
FLUSH PRIVILEGES;
exit
```
## Getting the files
### Cloning the github repository
```
wireflask@localhost ~/ $ git clone https://github.com/costagabbie/wireflaskadmin.git
```
The benefits of using this: An update is a `git pull` away, the downside is that you might be getting buggy software that will ruin your day.
## Creating the configuration
### For webapp
```
wireflask@localhost ~/ $ cd ~/wireflaskadmin/webapp
wireflask@localhost ~/ $ vim .env
```
and place the following content, replacing where is needed
```
WFADMIN_SECRET_KEY='INSERT YOUR SECRET KEY'
WFADMIN_RECAPTCHA_API_KEY='INSERT YOUR RECAPTCHA API KEY'
WFADMIN_RECAPTCHA_SITE_KEY='INSERT YOUR RECAPTCHA SITE KEY'
WFADMIN_SQLALCHEMY_DATABASE_URI='mysql+pymysql://wfadmin:abcd1234@localhost:3306/wfadmin'
WFADMIN_ENDPOINT_AUTOIP=N
WFADMIN_REBUILD_STARTUP=N
WFADMIN_DAEMON_HOST=127.0.0.1
WFADMIN_DAEMON_PORT=9929
WFADMIN_REBUILD_STARTUP=N
```
*Tip: You can symlink this file to ~/wireflaskadmin/daemon/.env this way you will have your configs in the same file.*
### For daemon
Same as above.
## Creating the virtual environments
### For webapp
```
wireflask@localhost ~/ $ cd ~/wireflaskadmin/webapp
wireflask@localhost ~/wireflaskadmin/webapp $ python3 -m venv .venv
```
### For daemon
```
wireflask@localhost ~/ $ cd ~/wireflaskadmin/daemon
wireflask@localhost ~/wireflaskadmin/daemon $ python3 -m venv .venv
```
## Installing the required dependencies
### For webapp
```
wireflask@localhost ~/ $ cd ~/wireflaskadmin/webapp
wireflask@localhost ~/wireflaskadmin/webapp $ source .venv/bin/activate
(.venv) wireflask@localhost ~/wireflaskadmin/webapp $ pip install -r requirements.txt
(.venv) wireflask@localhost ~/wireflaskadmin/webapp $ pip install gunicorn
(.venv) wireflask@localhost ~/wireflaskadmin/webapp $ deactivate
```
Note that we are using gunicorn as wsgi server, if you know what you're doing, you could use another one
### For daemon
```
wireflask@localhost ~/ $ cd ~/wireflaskadmin/daemon
wireflask@localhost ~/wireflaskadmin/daemon $ source .venv/bin/activate
(.venv) wireflask@localhost ~/wireflaskadmin/daemon $ pip install -r requirements.txt
(.venv) wireflask@localhost ~/wireflaskadmin/daemon $ deactivate
```
## Configuring the Web server
### nginx
```
root@localhost ~/ # cd /home/wireflask/wireflaskadmin/webapp/wfadmin
root@localhost /home/wireflask/wireflaskadmin/webapp/wfadmin/ # chmod 755 -R static
root@localhost /home/wireflask # cd /etc/nginx/sites-available
root@localhost /etc/nginx/sites-available # vim wfadmin
```
if you don't like vim, use whatever text editor you like to input the following content:
```
    server {
        server_tokens off;
        location static{
                alias /home/wireflask/wireflaskadmin/webapp/wfadmin/static;
        }
        location /{
                proxy_pass http://127.0.0.1:8000;
                include /etc/nginx/proxy_params;
                proxy_redirect off;
        }
        listen 80;
        listen [::]:80;
    }

```
Note that servername can be added, but it is left out intentionally, also **YOU SHOULD SERIOUSLY CONSIDER IMPLEMENTING SSL, with certbot it is really easy**
Now lets enable the site 
```
root@localhost /etc/nginx/sites-available # cd ../sites-enabled
root@localhost /etc/nginx/sites-enabled # ln -s ../sites-enabled/wfadmin wfadmin
root@localhost /etc/nginx/sites-enabled # nginx -t
```
if the nginx test pass then restart nginx
```
root@localhost /etc/nginx/sites-available # systemctl restart nginx
```

### Apache 
(To be wrote)

## Making SystemD units
### For webapp
On `/etc/systemd/system` create a file named `wfadmin.service` with the following content
```
[Unit]
Description=WireFlaskAdmin WebApp
After=mariadb.service
Requires=mariadb.service
[Service]
WorkingDirectory=/home/wireflask/wireflaskadmin/webapp
User=test
ExecStart=/home/wireflask/wireflaskadmin/webapp/.venv/bin/gunicorn -w 3 app:app
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
```
### For daemon
On `/etc/systemd/system` create a file named `wgflaskd.service` with the following content
```
[Unit]
Description=WireFlaskAdmin Daemon
After=mariadb.service
Requires=mariadb.service
[Service]
WorkingDirectory=/home/wireflask/wireflaskadmin/daemon
User=root
ExecStart=/home/wireflask/wireflaskadmin/daemon/.venv/bin/python3 main.py
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
```

## Enabling the webapp
Type the following commands (the stuff after #)
```
root@localhost /etc/systemd/system # systemctl daemon-reload
root@localhost /etc/systemd/system # systemctl enable wfadmin.service
root@localhost /etc/systemd/system # systemctl start wfadmin.service
root@localhost /etc/systemd/system # systemctl status wfadmin.service
```
If the service is up and running you can finish the installation by creating the tables on the database.
The tables can be created with a web browser by visiting the ip or hostname on /install, or simply use curl to do that
`curl 'http://127.0.0.1:8000/install'`
**Before starting the daemon(wgflaskd.service) it is important to have the tables created!**
## Enabling the daemon
```
root@localhost /etc/systemd/system # systemctl enable wgflaskd.service
root@localhost /etc/systemd/system # systemctl start wgflaskd.service
root@localhost /etc/systemd/system # systemctl status wgflaskd.service
```

That's it, the wireflaskadmin project should be up and running on your system. you can log-in with your operating system credentials and start configuring your Wireguard Endpoints/Peers