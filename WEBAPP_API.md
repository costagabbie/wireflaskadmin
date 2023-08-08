# Webapp API Documentation
The webapp api is pretty simple so far, currently the authentication need a username and password but an API key will be implemented
## /api/login
### Description
Like /login but returns just a string to make easy to use with curl on a shell script.
### Parameters
```
user= user name
pwd= password for the user
```
### Return
```
Success: HTTP 200 with a string '200'
Failure: HTTP 403.
```
## /api/endpoint/<pubkey>
### Description
Providing the "Wireguard Endpoint" public key it will return a configuration file.
Note:Since there's nowhere within the app to get the Private key it generates with a placeholder.
### Result
Success: HTTP 200 with the body being the configuration file.
Failure: HTTP 404
**Note: that the public key need to be passed in the url encoded as Base64URL because the key may have some characters that will interfere with the url(/+=).**
## /api/endpoint/<id>
### Description
Providing the primary key of the database entry for the "Wireguard Endpoint" it will return a configuration file.
Note that since there's nowhere within the app to get the Private key it generates with a placeholder.
### Result
Success: HTTP 200 with the body being the configuration file.
Failure: HTTP 404
## /api/peer/<pubkey>
### Optional parameter
routeall: 0 will have only the endpoint ip in the AllowedIPs, 1 will have the endpoint ip, plus all other peers that share the same endpoint
### Description
Providing the public key inserted for the "Wireguard Peer", it will return a configuration file for the peer, perhaps a future implementation could add an option to generate a Network Manager file or a zip file to be imported?
Note: Since there's nowhere within the app to get the Private key it generates with a placeholder.
### Result
Success: HTTP 200 with the body being the configuration file.
Failure: HTTP 404
**Note: The public key need to be passed in the url encoded as Base64URL because the key may have some characters that will interfere with the url(/+=).**
## /api/peer/<id>
### Optional parameter
routeall: 0 will have only the endpoint ip in the AllowedIPs, 1 will have the endpoint ip, plus all other peers that share the same endpoint
### Description
Providing the primary key of the database entry for the "Wireguard Peert" it will return a configuration file.
Note that since there's nowhere within the app to get the Private key it generates with a placeholder.
### Result
Success: HTTP 200 with the body being the configuration file.
Failure: HTTP 404