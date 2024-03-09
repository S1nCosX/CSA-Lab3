import logging


class DataBus:
    def __init__(self) -> None:
        self.value = 0


class OutputDevice:
    def __init__(self, databus: DataBus) -> None:
        self.CS = False
        self.databus = databus
        self.output_buffer: list[str] = []

    def set_cs(self, cs: bool):
        self.CS = cs

    def set_wr(self, wr: bool):
        if not wr:
            return
        if not self.CS:
            return
        logging.debug(f"output: {self.output_buffer} <-- '{chr(self.databus.value)}'")
        self.output_buffer.append(chr(self.databus.value))


class InputDevice:
    def __init__(self, databus: DataBus, input_buffer: list[str]) -> None:
        self.CS = False
        self.databus = databus
        self.input_buffer = input_buffer[::-1]

    def set_cs(self, cs: bool):
        self.CS = cs

    def set_oe(self, oe: bool):
        if not oe:
            return
        if not self.CS:
            return
        self.databus.value = ord(self.input_buffer.pop())
        logging.debug(f"input: {self.input_buffer} --> '{chr(self.databus.value)}'")


class RAM:
    def __init__(self, databus: DataBus) -> None:
        self.CS = False
        self.OE = False
        self.databus = databus
        self.data_address = 0
        self.mem: dict[int, int] = dict()

    def set_cs(self, cs: bool):
        self.CS = cs

    def set_data_addr(self, addr: int):
        self.data_address = addr
        self.set_oe(self.OE)

    def set_oe(self, oe: bool):
        self.OE = oe
        if not oe:
            return
        if not self.CS:
            return
        self.databus.value = self.mem.get(self.data_address, 0)

    def set_wr(self, wr: bool):
        if not wr:
            return
        if not self.CS:
            return
        self.mem[self.data_address] = self.databus.value


class DataPath:
    INPUT_ADDR = 0x10000000
    OUTPUT_ADDR = 0x10000001

    def __init__(self, input_buffer) -> None:
        self.databus = DataBus()
        self.output = OutputDevice(self.databus)
        self.input = InputDevice(self.databus, input_buffer)
        self.mem = RAM(self.databus)

        self.acc = 0
        self.acc_in = 0
        self.acc_out = False

        self.data_address = 0

    def latch_data_addr(self, addr: int):
        if addr == self.INPUT_ADDR:
            self.input.set_cs(True)
            self.output.set_cs(False)
            self.mem.set_cs(False)
        elif addr == self.OUTPUT_ADDR:
            self.input.set_cs(False)
            self.output.set_cs(True)
            self.mem.set_cs(False)
        else:
            self.input.set_cs(False)
            self.output.set_cs(False)
            self.mem.set_cs(True)
        self.mem.set_data_addr(addr)
        self.data_address = addr

    def set_wr(self, wr: bool):
        self.output.set_wr(wr)
        self.mem.set_wr(wr)

    def set_oe(self, oe: bool):
        self.input.set_oe(oe)
        self.mem.set_oe(oe)

    def set_acc_out(self, acc_out: bool):
        if acc_out:
            self.databus.value = self.acc
        self.acc_out = acc_out

    def set_acc_in(self, acc_in: int):
        self.acc_in = acc_in

    def latch_acc(self):
        self.acc = self.acc_in
        if self.acc_out:
            self.databus.value = self.acc

    def get_acc(self):
        return self.acc

    def get_data_out(self):
        return self.databus.value
