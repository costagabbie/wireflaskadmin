import signal
import socket
from select import select
from os import system,path
import sys
from subprocess import check_output
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from wgflaskd.config import Config
from wgflaskd.models import Endpoint,Peer,create_metadata
sys.path.append('../')
from common.types import CommandPacket, DaemonCommandType,str_to_command_packet


#SQLAlchemy Stuff
engine = create_engine(url=Config.SQLALCHEMY_DATABASE_URI)
create_metadata(engine)
Session = sessionmaker(bind=engine)
db = Session()

class DaemonSignalHandler:
  terminate = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, *args):
    self.terminate = True


#Auxiliary functions
def control_interface(action:DaemonCommandType,iface:int)->bool:
    match action:
        case DaemonCommandType.CMD_START:
            return system(f'systemctl start wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_STOP:
            return system(f'systemctl stop wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_RESTART:
            return system(f'systemctl stop wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_REBUILD:
            return create_config(iface)
        case DaemonCommandType.CMD_ENABLE:
            return system(f'systemctl enable wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_DISABLE:
            return system(f'systemctl disable wg-quick@wg{iface}') == 0


def create_keypair(iface:int)->bool:
    return check_output(f'wg genkey | tee /etc/wireguard/wg{iface}-privatekey | wg pubkey > /etc/wireguard/wg{iface}-publickey',shell=True) ==''


def create_config(iface:int)->bool:
    endpoint = db.query(Endpoint).filter_by(id=iface).first()
    if not endpoint:
        return False
    peers = db.query(Peer).filter_by(endpoint=endpoint.id).all()
    if not path.exists(f'/etc/wireguard/wg{iface}-privatekey'):
        create_keypair(iface)
    with open(f'wg{iface}-privatekey','r') as privkey_file:
        privatekey = privkey_file.readline()
    with open(f'wg{iface}-privatekey','r') as pubkey_file:
        publickey = pubkey_file.readline()
        if len(endpoint.public_key) == 0:
            endpoint.public_key = publickey
            db.commit() 
    with open(f'wg{iface}.conf','w') as config_file:
        write_endpoint(config_file,privatekey,endpoint)
        #Now we go to the peers if we have any
        if peers:
            for peer in peers:
                write_peer(config_file,peer)
        control_interface(DaemonCommandType.CMD_ENABLE,iface)
    return True

def write_endpoint(config_file,privatekey,endpoint):
    #Writing the bare minimum for interface
    config_file.write(
        f'''[Interface]
#Name = {endpoint.name}
Address={endpoint.address}
ListenPort={endpoint.listen_port}
PrivateKey={privatekey}
'''
    )
    #If we have a dns specified,write the dns
    if len(endpoint.dns) > 0:
        config_file.write(f'DNS={endpoint.dns}')
    #For routing table, if the table is -1 then we set to off, 
    # 0 means auto(default, don't need to specify), 
    # > 0 means a custom table that we need to write to the cfg
    if endpoint.routing_table == -1:
        config_file.write(f'Table=off')     
    elif endpoint.routing_table > 0:
        config_file.write(f'Table={endpoint.routing_table}')
    #If the MTU is above the minimum and smaller than the default maximum(1500)
    #we specify on the config file
    if 68 <= endpoint.mtu < 1500:
        config_file.write(f'MTU={endpoint.mtu}')
    #Checking and writing if we have Pre/Post up/down commands
    if len(endpoint.preup) > 0:
        config_file.write(f'PreUp={endpoint.preup}')
    if len(endpoint.postup) > 0:
        config_file.write(f'PostUp={endpoint.postup}')
    if len(endpoint.predown) > 0:
        config_file.write(f'PreDown={endpoint.predown}')
    if len(endpoint.postdown) >0:
        config_file.write(f'PostDown={endpoint.postdown}')

def write_peer(config_file,peer):
    config_file.write(
    f'''
[Peer]
#Name={peer.name}
AllowedIPs={peer.address}/{peer.netmask}
PublicKey={peer.public_key}
'''
    )
    if peer.keepalive > 0:
        config_file.write(f'PersistentKeepalive={peer.keepalive}')


def handle_packet(packet:CommandPacket)->bool:
    print(packet)
    #If we are controlling a specific interface
    if packet.Interface > 0:
        return control_interface(packet.CommandType,packet.Interface)
    #If we are not controlling a specific interface we iterate through
    #every single endpoint available and perform the action
    endpoints = db.query(Endpoint).all()
    #If any interface fail to be controlled, we return false
    success = True
    for endpoint in endpoints:
        if not control_interface(packet.CommandType,endpoint.id):
            success = False
    return success


def main():
    sighandler = DaemonSignalHandler()
    if Config.REBUILD_STARTUP.upper() =='Y':
        handle_packet(CommandPacket(DaemonCommandType.CMD_REBUILD,0))
        handle_packet(CommandPacket(DaemonCommandType.CMD_RESTART,0))
    #Initializing the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(0)
    server_socket.bind((Config.DAEMON_HOST, int(Config.DAEMON_PORT)))
    server_socket.listen()
    print("Waiting for connection")
    sockets_list = [server_socket]
    clients = {}
    while not sighandler.terminate:
        try:
            readable_sockets,_,_  = select(sockets_list,[],[],1)
            for notified_socket in readable_sockets:
                if notified_socket == server_socket:
                    client_connection, client_address = server_socket.accept()
                    client_connection.setblocking(0)
                    print(f"New connection established from {client_address}")
                    sockets_list.append(client_connection)
                    clients[client_connection] = client_address
                else:
                    data = notified_socket.recv(1024)
                    if not data:
                        print(f"Connection closed by {clients[notified_socket]}")
                        sockets_list.remove(notified_socket)
                        del clients[notified_socket]
                    else:
                        # Processing the command received
                        print(f"Received data from {clients[notified_socket]}")
                        #handle_packet(str_to_command_packet(data.decode('utf-8')))
                        print(str_to_command_packet(data.decode('utf-8')))
        except socket.error as e:
            print(e.strerror)
    print("Exiting")
if __name__ == '__main__':
    main()