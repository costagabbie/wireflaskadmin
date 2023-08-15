# wireflaskadmin
## Project description
Minimal wireguard configuration /management webapp.

The project is split into two parts(possibly three), the webapp and the daemon(and possibly an api agent)

The webapp should run as a normal user, since it's not a good idea to run an internet facing application as root, however the daemon is the part that manage wireguard configs, and the wg-quick services and it should run as root(because the daemon needs the privileges to read and write to /etc/wireguard and execute systemctl commands to manage the services).
## Project status
It's in early development stage, the webapp is pretty much done, just need some better exception handling and some UI/UX refinements, and also some extensive testing.
Feel free to contribute to the project, either with python code, unit tests, or html/css/js or even translating or improving this readme file, or even documentation.
## Security
### Automated tools scanning
The project has been scanned with Nikto and wapiti, no major issues has been found.
### No private key on the webapp
The webapp doesn't handle any private keys for an specific reason, if it is ever compromised, not having private keys will mitigate the damage that an attacker with a private key would have.
## Features
### Endpoint Management
Have entries for each endpoint(wireguard interface) that you host, private keys and pubkeys are created by the daemon with its own interface config, and only the pubkey is available for the webapp for security reasons.
### Peer Management
Each peer is linked to an endpoint, and you can manage each one of them, and once you tell the daemon to rebuild the configuration it will rebuild and restart the interface(s).
### Authentication
The authentication to change the configurations are provided by PAM, if someone wants to add support to LDAP please feel free to contribute.
### API
Web api that allows login and retrieval of Endpoint and Peer configurations already using wireguard format 
## Planned Features
- API Agent that poll the Web API and automatically deploy the provisioned configuration.
- reCaptcha(or some other captcha system) on login to make bruteforcing a bit more difficult.
- 2FA for that extra bit of security.
- Rate limiting
- LDAP authentication support
## Installation 
Read the INSTALL.md file
## Thanks
Special thanks for rahlskog,mingalsuo and Theros from linux.chat Discord server
