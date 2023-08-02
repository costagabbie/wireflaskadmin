from wfadmin.config import Config
import socket
from dataclasses import dataclass
from common.types import CommandPacket, DaemonCommandType,command_packet_to_str

def SendCommand(cmd_type: DaemonCommandType, iface: int) -> bool:
    try:
        packet = CommandPacket(cmd_type, iface)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_ip = socket.gethostbyname(Config.DAEMON_HOST)
        s.connect((remote_ip, int(Config.DAEMON_PORT)))
        s.sendall(command_packet_to_str(packet).encode('utf-8'))
        s.close()
        return True
    except socket.error:
        return False
    except socket.gaierror:
        return False
