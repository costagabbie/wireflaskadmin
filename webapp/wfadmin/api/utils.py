from wfadmin.models import Endpoint,Peer


def writeEndpointInterface(endpoint:Endpoint)->str:
    interfaceSection = \
    f'''[Interface]
#Name = {endpoint.name}
Address={endpoint.address}
ListenPort={endpoint.listen_port}
PrivateKey=###REPLACE_ME_WITH_PRIVATE_KEY###
'''
    if endpoint.routing_table == -1:
        interfaceSection+=f'Table=off\n'
    elif endpoint.routing_table > 0:
        interfaceSection+=f'Table={endpoint.routing_table}\n'
    if 68 <= endpoint.mtu < 1500:
        interfaceSection+=f'MTU={endpoint.mtu}\n'
    if len(endpoint.preup) > 0:
        interfaceSection+=f'PreUp={endpoint.preup}\n'
    if len(endpoint.postup) > 0:
        interfaceSection+=f'PostUp={endpoint.postup}\n'
    if len(endpoint.predown) > 0:
        interfaceSection+=f'PreDown={endpoint.predown}\n'
    if len(endpoint.postdown) >0:
        interfaceSection+=f'PostDown={endpoint.postdown}\n'


    return interfaceSection
def writeEndpointPeer(peer:Peer)->str:
    peerSection = f'''
[Peer]
#Name={peer.name}
AllowedIPs={peer.address}/{peer.netmask}
PublicKey={peer.public_key}
'''
    if peer.keepalive > 0:
        peerSection+=f'PersistentKeepalive={peer.keepalive}'
    return peerSection

def writePeer(peer:Peer)->str:
    peerConfig=f'''[Interface]
PrivateKey = ###REPLACE_ME_WITH_PEER_PRIVATE_KEY###
Address = 10.0.0.0/32

[Peer]
PublicKey = {peer.endpoint_pubkey()}
AllowedIPs = {peer.address}/{peer.netmask}
Endpoint = {peer.endpoint_address()}
'''
    if peer.keepalive >0:
        peerConfig+=f'PersistentKeepalive = {peer.keepalive}'
    return peerConfig
