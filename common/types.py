from enum import Enum
from dataclasses import dataclass

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
