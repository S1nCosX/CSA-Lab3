import logging
import sys

from isa import Instruction, parce_instruction
from control_unit import ControlUnit

def parse_isa(lines: list[str]) -> list[Instruction]:
    res: list[Instruction] = []
    for line in lines:
        res.append(parce_instruction(line)) 
    return res
    
def main(args: list[str]): # основная функция
    with open(args[0], 'r') as file:
        program = parse_isa(file.readlines())
    
    with open(args[1]) as inp:
        input_data = [*(inp.readline())]

    control_unit = ControlUnit(input_data, program)
    try:
        while True:
            control_unit.execute_next()
    except StopIteration:
        pass
    print("".join(control_unit.datapath.output.output_buffer))


if __name__ == "__main__":
    assert len(sys.argv[1:]) == 2, "machine.py <code_file> <input_file>"
    main(sys.argv[1:])
