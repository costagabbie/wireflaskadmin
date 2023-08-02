from enum import IntEnum
from dataclasses import dataclass

#Classes
@dataclass
class CommandPacket:
    CommandType: int
    Interface: int


class DaemonCommandType(IntEnum):
    CMD_START = 0
    CMD_STOP = 1
    CMD_RESTART = 2
    CMD_REBUILD = 3
    CMD_ENABLE = 4
    CMD_DISABLE = 5

def command_packet_to_str(packet:CommandPacket)->str:
    return f'{packet.CommandType},{packet.Interface}\n'

def str_to_command_packet(s:str)->CommandPacket:
    if not ',' in s:
        return CommandPacket(-1,0)
    try:
        cmd = int(s.split(',')[0])
    except ValueError:
        cmd = -1
    try:
        iface = int(s.split(',')[1])
    except ValueError:
        iface = 0
    return CommandPacket(cmd,iface)