from wfadmin.config import Config
from wfadmin.translations.default import strings
from enum import Enum
import socket
import pickle
from dataclasses import dataclass
import sys
from common.types import CommandPacket, DaemonCommandType

def SendCommand(cmd_type: DaemonCommandType, iface: int) -> bool:
    try:
        packet = CommandPacket(cmd_type, iface)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_ip = socket.gethostbyname(Config.DAEMON_HOST)
        s.connect((remote_ip, int(Config.DAEMON_PORT)))
        s.sendall(pickle.dumps(CommandPacket(cmd_type,iface)))
        s.close()
        return True
    except socket.error:
        return False
    except socket.gaierror:
        return False
