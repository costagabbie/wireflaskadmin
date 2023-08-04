import argparse
import signal
import socket
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from select import select
from os import system,path
from subprocess import check_output,CalledProcessError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from wgflaskd.config import Config
from wgflaskd.models import Endpoint,Peer,create_metadata
sys.path.append('../')
from common.types import CommandPacket, DaemonCommandType,str_to_command_packet


#SQLAlchemy Stuff
engine = create_engine(url=Config.SQLALCHEMY_DATABASE_URI)
create_metadata(engine)
Session = sessionmaker(bind=engine)
db = Session()

logger = logging.getLogger()
handler = RotatingFileHandler('/var/log/wgflaskd.log', maxBytes=1024000,backupCount=5)
logger.addHandler(handler)

class DaemonSignalHandler:
    terminate = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_sigint)
        signal.signal(signal.SIGTERM, self.exit_sigterm)
    def exit_sigint(self, *args):
        logging.error(f'wgflaskd received SIGINT and is now terminating')
        self.terminate = True
    def exit_sigterm(self, *args):
        logging.info(f'wgflaskd received SIGTERM and is now terminating')
        self.terminate = True


#Auxiliary functions
def control_interface(action:DaemonCommandType,iface:int)->bool:
    match action:
        case DaemonCommandType.CMD_START:
            logging.debug(f'control_interface executed :systemctl start wg-quick@wg{iface}')
            return system(f'systemctl start wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_STOP:
            logging.debug(f'control_interface executed :systemctl stop wg-quick@wg{iface}')
            return system(f'systemctl stop wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_RESTART:
            logging.debug(f'control_interface executed :systemctl restart wg-quick@wg{iface}')
            return system(f'systemctl restart wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_REBUILD:
            logging.debug(f'control_interface called create_config({iface})')
            return create_config(iface)
        case DaemonCommandType.CMD_ENABLE:
            logging.debug(f'control_interface executed :systemctl enable wg-quick@wg{iface}')
            return system(f'systemctl enable wg-quick@wg{iface}') == 0
        case DaemonCommandType.CMD_DISABLE:
            logging.debug(f'control_interface executed :systemctl disable wg-quick@wg{iface}')
            return system(f'systemctl disable wg-quick@wg{iface}') == 0

def is_interface_enabled(iface:str)->bool:
    return system(f'systemctl is-enabled wg-quick@wg{iface}') == 0

def create_keypair(iface:int)->bool:
    try:
        ret = check_output(f'wg genkey | tee /etc/wireguard/wg{iface}-privatekey | wg pubkey > /etc/wireguard/wg{iface}-publickey',shell=True) 
        logging.info(f'create_keypair returned {ret}')
        return ret ==''
    except CalledProcessError as e:
        logging.error(f'create_keypair->check_output raised an exception:{e.output}')
        return False


def create_config(iface:int)->bool:
    endpoint = db.query(Endpoint).filter_by(id=iface).first()
    if not endpoint:
        return False
    peers = db.query(Peer).filter_by(endpoint=endpoint.id).all()
    if is_interface_enabled(iface):
        control_interface(DaemonCommandType.CMD_DISABLE,iface)
    if not path.exists(f'/etc/wireguard/wg{iface}-privatekey'):
        create_keypair(iface)
    try:
        with open(f'/etc/wireguard/wg{iface}-privatekey','r') as privkey_file:
            privatekey = privkey_file.readline()
    except OSError as e:
        logger.error(f'Failed to read private key file:{e}')
        return False
    try:
        with open(f'/etc/wireguard/wg{iface}-privatekey','r') as pubkey_file:
            publickey = pubkey_file.readline()
            if endpoint.public_key is None:
                endpoint.public_key = publickey
                db.commit()
    except OSError as e:
        logger.error(f'Failed to read public key file:{e}') 
        return False 
    except OperationalError as e:
        logger.error(f'Failed to update endpoint record with public key:{e}')
        return False
    try:       
        with open(f'/etc/wireguard/wg{iface}.conf','w') as config_file:
            write_endpoint(config_file,privatekey,endpoint)
            #Now we go to the peers if we have any
            if peers:
                for peer in peers:
                    write_peer(config_file,peer)
            control_interface(DaemonCommandType.CMD_ENABLE,iface)
            logging.info(f'Log saved to /etc/wireguard/wg{iface}.conf')
        return True
    except OSError as e:
        logger.error(f'Failed to write wireguard configuration file:{e}')
        return False

def write_endpoint(config_file,privatekey,endpoint):
    #Writing the bare minimum for interface
    logging.debug(f'Writing Endpoint={repr(endpoint)}')
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
    logging.debug(f'Writing Peer={repr(peer)}')
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
    logging.debug(f'CommandPacket({packet.CommandType},{packet.Interface})')
    #If we are controlling a specific interface
    if packet.Interface > 0:
        success = control_interface(packet.CommandType,packet.Interface)
        if not success:
            logger.error(f'control_interface({packet.CommandType},{endpoint.id}) returned false.')
        return success
    #If we are not controlling a specific interface we iterate through
    #every single endpoint available and perform the action
    endpoints = db.query(Endpoint).all()
    #If any interface fail to be controlled, we return false
    success = True
    for endpoint in endpoints:
        if not control_interface(packet.CommandType,endpoint.id):
            logger.error(f'control_interface({packet.CommandType},{endpoint.id}) returned false.')
            success = False
    return success


def main():
    sighandler = DaemonSignalHandler()
    parser = argparse.ArgumentParser(description='WireFlaskAdmin daemon')
    parser.add_argument('-ll', '--loglevel', dest='loglevel', help='Sets the log level(normal, verbose, debug)',type=str,default='normal')
    args= parser.parse_args()
    if args.loglevel == 'verbose':
        logger.setLevel(logging.INFO)
    elif args.loglevel == 'debug':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)
    logger.info(f'Starting up at{datetime.utcnow}')
    if Config.REBUILD_STARTUP.upper() =='Y':
        logger.info(f'Rebuilding all the endpoint configurations.')
        handle_packet(CommandPacket(DaemonCommandType.CMD_REBUILD,0))
        handle_packet(CommandPacket(DaemonCommandType.CMD_RESTART,0))
    #Initializing the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(0)
    server_socket.bind((Config.DAEMON_HOST, int(Config.DAEMON_PORT)))
    server_socket.listen()
    logger.info('Waiting for connection')
    sockets_list = [server_socket]
    clients = {}
    while not sighandler.terminate:
        try:
            readable_sockets,_,_  = select(sockets_list,[],[],1)
            for notified_socket in readable_sockets:
                if notified_socket == server_socket:
                    client_connection, client_address = server_socket.accept()
                    client_connection.setblocking(0)
                    logger.info(f'New connection established from {client_address}')
                    sockets_list.append(client_connection)
                    clients[client_connection] = client_address
                else:
                    data = notified_socket.recv(1024)
                    if not data:
                        logger.info(f'Connection closed by {clients[notified_socket]}')
                        sockets_list.remove(notified_socket)
                        del clients[notified_socket]
                    else:
                        # Processing the command received
                        logger.info(f'Received data from {clients[notified_socket]}')
                        logger.debug(f'Data received= {data.decode("utf-8")}')
                        handle_packet(str_to_command_packet(data.decode('utf-8')))
        except socket.error as e:
            logger.error(e.strerror)
    logger.info('Exiting')
if __name__ == '__main__':
    main()