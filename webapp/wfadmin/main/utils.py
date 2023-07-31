from wfadmin.config import Config
from wfadmin.translations.default import strings
from enum import Enum
import socket
import pickle
from dataclasses import dataclass


class DaemonCommandType(Enum):
    CMD_START = 0
    CMD_STOP = 1
    CMD_RESTART = 2
    CMD_REBUILD = 3


@dataclass
class CommandPacket:
    CommandType: int
    Interface: int


def SendCommand(cmd_type: DaemonCommandType, iface: int) -> bool:
    try:
        packet = CommandPacket(cmd_type, iface)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_ip = socket.gethostbyname(Config.DAEMON_HOST)
        s.connect((remote_ip, Config.DAEMON_PORT))
        data = pickle.dumps(packet)
        s.sendall(data)
        response = s.recv(2)
        s.close()
        return response == "OK"
    except socket.error:
        print("Could not create the socket")
        return False
    except socket.gaierror:
        print("Hostname could not be resolved. Exiting")
        return False
