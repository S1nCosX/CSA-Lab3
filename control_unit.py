from __future__ import annotations

import enum
import logging

from isa import ArgType, Instruction, Opcode
from datapath import DataPath


class LogicError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ControlUnit:
    class Stage(enum.Enum):
        INSTR_FETCH = 0
        ARG_FETCH = 1
        EXECUTION = 2

    class PCMux(enum.Enum):
        INC = 1
        ARG = 2

    class ArgMux(enum.Enum):
        IMM = 1
        DATA = 2

    def __init__(self, input_buffer: list[str], program: list[Instruction]) -> None:
        self.datapath = DataPath(input_buffer)

        self.sel_arg: ControlUnit.ArgMux = ControlUnit.ArgMux.IMM
        self.sel_next: ControlUnit.PCMux = ControlUnit.PCMux.INC

        self.tick_cnt: int = 0

        self.step_cnt: int = 0
        self.stage: ControlUnit.Stage = ControlUnit.Stage.INSTR_FETCH

        self.program_counter: int = -1
        self.program: list[Instruction] = program

        # добавляем в память переменные и метки
        program_offset = self.prepare_for_work()
        self.program = self.program[self.program_counter:]
        self.program_counter -= self.program_counter
        self.tick_cnt = 0

        self.N: bool = False
        self.Z: bool = True

    def prepare_for_work(self) -> int:
        if (self.program[0].opcode == Opcode.preload):
            while self.program[self.program_counter].opcode != Opcode.program:
                self.execute_next()
            return
        else:
            return 0

    def get_arg(self) -> int:
        if self.sel_arg == ControlUnit.ArgMux.IMM:
            arg = self.program[self.program_counter].arg
            if arg is None:
                return 0
            return arg

        if self.sel_arg == ControlUnit.ArgMux.DATA:
            return self.datapath.get_data_out()

        raise LogicError(message="Unknown value in sel_arg")

    def latch_pc(self):
        if self.sel_next == ControlUnit.PCMux.INC:
            self.program_counter += 1
        if self.sel_next == ControlUnit.PCMux.ARG:
            self.program_counter = self.get_arg()

    def next_stage(self):
        self.stage = ControlUnit.Stage((self.stage.value + 1) % len(ControlUnit.Stage))
        self.step_cnt = 0

    def instr_fetch(self) -> int:
        # rise
        self.datapath.set_acc_out(False)
        self.datapath.set_oe(False)
        self.datapath.set_wr(False)
        self.latch_pc()
        logging.debug("")
        logging.debug(f"Fetched: {self.program[self.program_counter]}")
        # fall
        self.sel_next = ControlUnit.PCMux.INC
        self.sel_arg = ControlUnit.ArgMux.IMM

        self.next_stage()
        return 1

    def arg_fetch(self) -> int:
        instr = self.program[self.program_counter]

        if instr.arg is None or instr.arg_type == ArgType.IMMEDIATE:
            logging.debug("Arg fetch stage skipped")
            self.next_stage()
            return 0

        if self.step_cnt == 0:
            # rise
            self.datapath.latch_data_addr(self.get_arg())
            # fall
            self.sel_arg = ControlUnit.ArgMux.DATA
            self.datapath.set_oe(True)

            if instr.arg_type == ArgType.INDIRECT:
                self.step_cnt += 1
            else:
                self.next_stage()

            return 1

        if self.step_cnt == 1 and instr.arg_type == ArgType.INDIRECT:
            # rise
            self.datapath.latch_data_addr(self.get_arg())
            self.next_stage()
            return 1

        raise LogicError(message=f"Illegal combination of step({self.step_cnt}) and ArgType({instr.arg_type.name})")

    def set_flags(self, val: int):
        self.Z = val == 0
        self.N = val < 0

    def execute(self) -> int:
        instr = self.program[self.program_counter]
        to_acc = False
        match instr.opcode:
            case Opcode.INC:
                self.datapath.set_acc_in(self.datapath.get_acc() + 1)
                self.set_flags(self.datapath.get_acc() + 1)
                to_acc = True
            case Opcode.DEC:
                self.datapath.set_acc_in(self.datapath.get_acc() - 1)
                self.set_flags(self.datapath.get_acc() - 1)
                to_acc = True
            case Opcode.JMP:
                self.sel_next = ControlUnit.PCMux.ARG
            case Opcode.JZ:
                if self.Z:
                    self.sel_next = ControlUnit.PCMux.ARG
            case Opcode.JNZ:
                if not self.Z:
                    self.sel_next = ControlUnit.PCMux.ARG
            case Opcode.SETG:
                self.datapath.set_acc_in(not self.Z and not self.N)
                self.set_flags(not self.Z and not self.N)
                to_acc = True
            case Opcode.SETL:
                self.datapath.set_acc_in(not self.Z and self.N)
                self.set_flags(not self.Z and self.N)
                to_acc = True
            case Opcode.SETE:
                self.datapath.set_acc_in(self.Z and not self.N)
                self.set_flags(self.Z and not self.N)
                to_acc = True
            case Opcode.CMP:
                self.set_flags(self.datapath.get_acc() - self.get_arg())
            case Opcode.LD:
                self.datapath.set_acc_in(self.get_arg())
                self.set_flags(self.get_arg())
                to_acc = True
            case Opcode.ST:
                # rise
                self.datapath.latch_data_addr(self.get_arg())
                self.datapath.set_oe(False)
                self.datapath.set_acc_out(True)
                # fall
                self.datapath.set_wr(True)
            case Opcode.ADD:
                self.datapath.set_acc_in(self.datapath.get_acc() + self.get_arg())
                self.set_flags(self.datapath.get_acc() + self.get_arg())
                to_acc = True
            case Opcode.SUB:
                self.datapath.set_acc_in(self.datapath.get_acc() - self.get_arg())
                self.set_flags(self.datapath.get_acc() - self.get_arg())
                to_acc = True
            case Opcode.MUL:
                self.datapath.set_acc_in(self.datapath.get_acc() * self.get_arg())
                self.set_flags(self.datapath.get_acc() * self.get_arg())
                to_acc = True
            case Opcode.DIV:
                self.datapath.set_acc_in(self.datapath.get_acc() // self.get_arg())
                self.set_flags(self.datapath.get_acc() // self.get_arg())
                to_acc = True
            case Opcode.REM:
                self.datapath.set_acc_in(self.datapath.get_acc() % self.get_arg())
                self.set_flags(self.datapath.get_acc() % self.get_arg())
                to_acc = True
            case Opcode.NEG:
                self.datapath.set_acc_in(-self.datapath.get_acc())
                self.set_flags(-self.datapath.get_acc())
                to_acc = True
            case Opcode.AND:
                self.datapath.set_acc_in(self.datapath.get_acc() & self.get_arg())
                self.set_flags(self.datapath.get_acc() & self.get_arg())
                to_acc = True
            case Opcode.NOT:
                res = self.datapath.get_acc() == 0
                self.datapath.set_acc_in(res)
                self.set_flags(res)
                to_acc = True
            case Opcode.OR:
                self.datapath.set_acc_in(self.datapath.get_acc() | self.get_arg())
                self.set_flags(self.datapath.get_acc() | self.get_arg())
                to_acc = True
            case Opcode.HLT:
                raise StopIteration()
        if to_acc:
            self.datapath.latch_acc()
        self.next_stage()
        return 1

    def execute_next(self):
        cur_op = self.program[self.program_counter].__str__()
        print(cur_op, ':', self.datapath.acc)
        while (cur_op == self.program[self.program_counter].__str__()):
            self.tick()

    def tick(self):
        logging.debug("%s", self)
        res = 0
        match self.stage:
            case ControlUnit.Stage.INSTR_FETCH:
                res = self.instr_fetch()
            case ControlUnit.Stage.ARG_FETCH:
                res = self.arg_fetch()
            case ControlUnit.Stage.EXECUTION:
                res = self.execute()
        self.tick_cnt += res

    def __str__(self) -> str:
        return (
            "TICK: {:5} STAGE: {:11} ACC: {:10} PC: {:3} DATA_ADDR: {:10} ARG: {:10} DATA_BUS: {:10} N|Z: {}|{}".format(
                self.tick_cnt,
                self.stage.name,
                self.datapath.acc,
                self.program_counter,
                self.datapath.data_address,
                self.get_arg(),
                self.datapath.databus.value,
                int(self.N),
                int(self.Z),
            )
        )
