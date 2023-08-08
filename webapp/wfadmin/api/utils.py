from wfadmin.models import Endpoint, Peer


def write_endpoint_interface(endpoint: Endpoint) -> str:
    interface_section = f"""[Interface]
#Name = {endpoint.name}
Address={endpoint.address}
ListenPort={endpoint.listen_port}
PrivateKey=###REPLACE_ME_WITH_PRIVATE_KEY###
"""
    if endpoint.routing_table == -1:
        interface_section += f"Table=off\n"
    elif endpoint.routing_table > 0:
        interface_section += f"Table={endpoint.routing_table}\n"
    if 68 <= endpoint.mtu < 1500:
        interface_section += f"MTU={endpoint.mtu}\n"
    if len(endpoint.preup) > 0:
        interface_section += f"PreUp={endpoint.preup}\n"
    if len(endpoint.postup) > 0:
        interface_section += f"PostUp={endpoint.postup}\n"
    if len(endpoint.predown) > 0:
        interface_section += f"PreDown={endpoint.predown}\n"
    if len(endpoint.postdown) > 0:
        interface_section += f"PostDown={endpoint.postdown}\n"

    return interface_section


def write_endpoint_peer(peer: Peer) -> str:
    peer_section = f"""
[Peer]
#Name={peer.name}
AllowedIPs={peer.address}/{peer.netmask}
PublicKey={peer.public_key}
"""
    if peer.keepalive > 0:
        peer_section += f"PersistentKeepalive={peer.keepalive}"
    return peer_section


def write_peer(peer: Peer,route_all:bool) -> str:
    allowed_ip = ''
    #If we want the config to allow the peer to reach another peer
    if route_all:
        allowed_ip = peer.endpoint_address()+','
        all_peers = Peer.query.filter_by(endpoint=peer.endpoint).all()
        for routable_peer in all_peers:
            if routable_peer.id != peer.id:
                allowed_ip += f'{routable_peer.address}/{routable_peer.netmask},'
        allowed_ip = allowed_ip[:-1] #remove the last ','
    else:
        allowed_ip = peer.endpoint_address()
    peer_config = f"""[Interface]
PrivateKey = ###REPLACE_ME_WITH_PEER_PRIVATE_KEY###
Address = {peer.address}/{peer.netmask}

[Peer]
PublicKey = {peer.endpoint_pubkey()}
AllowedIPs = {allowed_ip}
Endpoint = {peer.endpoint_ipaddress()}
"""
    if peer.keepalive > 0:
        peer_config += f"PersistentKeepalive = {peer.keepalive}"
    return peer_config
