import signal
import socket
from os import system,path
from enum import Enum
from dataclasses import dataclass
import pickle
from subprocess import check_output
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from wgflaskd.config import Config
from wgflaskd.models import Endpoint,Peer,create_metadata

print(f'{Config.SQLALCHEMY_DATABASE_URI}, {Config.DAEMON_HOST}, {Config.DAEMON_PORT}')
#SQLAlchemy Stuff
engine = create_engine(url=Config.SQLALCHEMY_DATABASE_URI)
create_metadata(engine)
Session = sessionmaker(bind=engine)
db = Session()

#Classes
@dataclass
class CommandPacket:
    CommandType: int
    Interface: int


class DaemonCommandType(Enum):
    CMD_START = 0
    CMD_STOP = 1
    CMD_RESTART = 2
    CMD_REBUILD = 3
    CMD_ENABLE = 4
    CMD_DISABLE = 5


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
            #return system(f'systemctl start wg-quick@wg{iface}') == 0
            print(f"systemctl start wg-quick@wg{iface}")
            return True
        case DaemonCommandType.CMD_STOP:
            #return system(f'systemctl stop wg-quick@wg{iface}') == 0
            print(f'systemctl stop wg-quick@wg{iface}')
            return True
        case DaemonCommandType.CMD_RESTART:
            #return system(f'systemctl stop wg-quick@wg{iface}') == 0
            print(f'systemctl restart wg-quick@wg{iface}')
            return True
        case DaemonCommandType.CMD_REBUILD:
            return create_config(iface)
        case DaemonCommandType.CMD_ENABLE:
            #return system(f'systemctl enable wg-quick@wg{iface}') == 0
            print(f'systemctl enable wg-quick@wg{iface}')
            return True
        case DaemonCommandType.CMD_DISABLE:
            #return system(f'systemctl disable wg-quick@wg{iface}') == 0
            print(f'systemctl disable wg-quick@wg{iface}')
            return True
    

def create_keypair(iface:int)->bool:
    return check_output(f'wg genkey | tee wg{iface}-privatekey | wg pubkey > wg{iface}-publickey',shell=True) ==''


def create_config(iface:int)->bool:
    endpoint = db.query(Endpoint).filter_by(id=iface).first()
    if not endpoint:
        return False
    peers = db.query(Peer).filter_by(endpoint=endpoint.id).all()
    if not path.exists(f'wg{iface}-privatekey'):
        create_keypair(iface)
    with open(f'wg{iface}-privatekey','r') as privkey_file:
        privatekey = privkey_file.readline()
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
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((Config.DAEMON_HOST, int(Config.DAEMON_PORT)))
    while not sighandler.terminate:
        print("Waiting for connection")
        server_socket.listen() 
        client_connection,addr = server_socket.accept() 
        print(f"Connection from {addr} accepted")
        while True:
            data_recv = client_connection.recv(1024) 
            if data_recv:
                try:
                    print(data_recv)
                    if handle_packet(CommandPacket(int(data_recv.decode('utf-8').split(',')[0]),int(data_recv.decode('utf-8').split(',')[1]))):
                        client_connection.send(str("OK").encode())
                        client_connection.close()
                        break
                    else:
                        client_connection.send(str("KO").encode())
                        client_connection.close()
                        break
                except BrokenPipeError:
                    print("Failed to send data")
                except TypeError:
                    print("Malformed request")
                    client_connection.close()


            
if __name__ == '__main__':
    main()