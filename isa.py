import enum
import re

from config import WORD_SIZE 

class Opcode(enum.StrEnum):
    preload = 'preload'
    program = 'program'
    # zero operand comand
    HLT = 'HLT'
    NEG = 'NEG'
    NOT = 'NOT'
    # ---
    SETE = 'SETE'
    SETG = 'SETG'
    SETL = 'SETL'

    # one operand comand
    INC = 'INC'
    DEC = 'DEC'
    # ---
    JMP = 'JMP'
    JZ = 'JZ'
    JNZ = 'JNZ'
    # ---
    ADD = 'ADD'
    SUB = 'SUB'
    MUL = 'MUL'
    DIV = 'DIV'
    REM = 'REM'
    # ---
    LD = 'LD'
    ST = 'ST'
    # ---
    AND = 'AND'
    OR = 'OR'
    # ---
    CMP = 'CMP'

class ArgType(enum.StrEnum):
    IMMEDIATE = "IMMEDIATE"
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"


class Instruction:
    def __init__(self, opcode: Opcode, arg: int | 
                None = None, arg_type: ArgType = ArgType.DIRECT, line: int | 
                None = None
                ) -> None:
        self.opcode = opcode
        self.arg = arg
        self.arg_type = arg_type
        self.line = line

    def __str__(self) -> str:
        return f"{self.opcode.name:<4} " + (
            f"{'[' + self.arg_type.name + ']':<11} {self.arg}" if self.arg is not None else ""
        )
    
def parce_instruction(string: str) -> Instruction:
    string = re.sub(r'\s+', " ", string[:-1])
    if (string.split(" ")[0] != 'preload:' and string.split(" ")[0] != 'program:'):
        opcode: Opcode = Opcode(string.split(" ")[0])
        arg_type: ArgType = ArgType(string.split(" ")[1][1:-1])
        arg: int = int(string.split(" ")[2])
        return Instruction(opcode=opcode, arg_type=arg_type, arg=arg)
    return Instruction(opcode=Opcode(string[:-1]))
