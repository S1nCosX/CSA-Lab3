import re
import sys

from isa import Instruction, Opcode, ArgType

# --предобработка ввода--
def preprocessing(sorce: str) -> str: # основная функция подраздела
    lines: list[str] = sorce.splitlines()
    strip_lines = map(str.strip, lines)
    remove_empty_lines = filter(bool, strip_lines)
    remove_commas = map(lambda s: s.replace("','", str(ord(','))).replace(',', ' '), remove_empty_lines)
    remove_space = map(lambda s: re.sub(r'\s+', ' ', s), remove_commas)
    return '\n'.join(remove_space)

class Translated_data:
    def __init__(self) -> None:
        self.input_addr = 0x10000000
        self.output_addr = 0x10000001

        self.data_start = 0x20000000
        self.data_end = 0x2FFFFFFF
        self.free_data = self.data_start

        self.mem_start = 0
        self.mem_end = 0x0FFFFFFF
        self.mem_cur = self.mem_start

        self.preload: list[Instruction] = []
        self.program: list[Instruction] = []

        self.var_table: dict[str, int] = {}
        self.var_table['#STDOUT'] = self.output_addr
        self.var_table['#STDIN'] = self.input_addr
        pass

    def _input_data_string(self, varname: str, value: str):
        assert value[0] == '"' and value[-1] == '"' and value.count('"') == 2, 'неправильный формат значения, значение строго: "val"'
        assert self.free_data + len(value) + 1 < self.data_end, 'Закончилась память'
        value = value[1:-1]
        self.var_table[varname] = self.free_data
        for i in value:
            self.preload.append(Instruction(opcode=Opcode.LD, arg=ord(i), arg_type=ArgType.IMMEDIATE))
            self.preload.append(Instruction(opcode=Opcode.ST, arg=self.free_data, arg_type=ArgType.IMMEDIATE))
            self.free_data += 1
        self.preload.append(Instruction(opcode=Opcode.LD, arg=0, arg_type=ArgType.IMMEDIATE))
        self.preload.append(Instruction(opcode=Opcode.ST, arg=self.free_data, arg_type=ArgType.IMMEDIATE))
        self.free_data += 1

    def _input_data_int(self, varname: str, value: int):
        assert self.free_data + 1 < self.data_end, 'Закончилась память'
        self.var_table[varname] = self.free_data
        self.preload.append(Instruction(opcode=Opcode.LD, arg=value, arg_type=ArgType.IMMEDIATE))
        self.preload.append(Instruction(opcode=Opcode.ST, arg=self.free_data, arg_type=ArgType.IMMEDIATE))
        self.free_data += 1

    def _input_data_char(self, varname: str, value: str):
        assert value.find("'") == 2 and len(value) == 3, 'Неправильный формат char у переменной' + varname
        value = value[1]
        assert self.free_data + len(value) + 1 < self.data_end, 'Закончилась память'
        self.var_table.append(varname, self.free_data)
        self.preload.append(Instruction(opcode=Opcode.LD, arg=ord(value), arg_type=ArgType.IMMEDIATE))
        self.preload.append(Instruction(opcode=Opcode.ST, arg=self.free_data, arg_type=ArgType.IMMEDIATE))
        self.free_data += 2

    def _input_comand(self, op: str, arg_type: str | None=None, arg: str | None=None):
        if (arg_type == None):
            self.program.append(Instruction(opcode=Opcode(op), arg=0, arg_type=ArgType.DIRECT, line=self.mem_cur))
        else:
            if (arg.isnumeric()):
                self.program.append(Instruction(opcode=Opcode(op), arg=arg, arg_type=ArgType(arg_type), line=self.mem_cur))
            else:
                self.program.append(Instruction(opcode=Opcode(op), arg=self.var_table[arg], arg_type=ArgType(arg_type), line=self.mem_cur))
        self.mem_cur += 1

    def _input_mark(self, markname: str):
        self.preload.append(Instruction(opcode=Opcode.LD, arg=self.mem_cur, arg_type=ArgType.IMMEDIATE))
        self.preload.append(Instruction(opcode=Opcode.ST, arg=self.free_data, arg_type=ArgType.IMMEDIATE))
        self.var_table[markname] = self.free_data
        self.free_data += 1
        self.mem_cur += 1

# --Основная функция--
def process(code: str, text_start: int, text_end: int, data_start: int, data_end: int) -> Translated_data:
    out_data: Translated_data = Translated_data()
    if (data_start != None):
        assert data_end != None, "Что-то пошло не так, data_start не None, но data_end да"
        
        for i in code[data_start:data_end].split("\n"):
            assert len(i.split(':')) == 2, 'У декларирования данных формат <varname>:<value>' 
            varname, value = i.split(':')
            
            if value[0] == '"':
                out_data._input_data_string(varname, value)
            elif value[0] == "'":
                out_data._input_data_char(varname, value)
            else:
                out_data._input_data_int(varname, int(value))

    for i in code[text_start:text_end].split("\n"):
        assert i[0] == '.' or len(i.split(' ')) == 1 or len(i.split(' ')) == 3, "У команд формат <comand> [optional]<arg> или .name если это метка"
        if (i[0] == '.'):
            out_data._input_mark(i)
        elif (len(i.split(' ')) == 1):
            out_data._input_comand(i)
        else:
            out_data._input_comand(i.split(' ')[0], i.split(' ')[1], i.split(' ')[2])

    return out_data

def main(args):
    source_path, target_path = args

    with open(source_path, "rt", encoding="utf-8") as file:
        source = file.read()

    code = preprocessing(source)
    text_index = code.find('section .text:')

    # получение индексов для считываний
    assert text_index != -1, "Должна быть обязательно cекция .text"
    text_start, text_end = text_index + len('section .text:') + 1, None
    data_start, data_end = None, None

    data_index = code.find('section .data:')
    if (data_index == -1):
        text_end = len(source)
    else:
        data_start = data_index + len('section .data:') + 1
        if (data_index < text_index):
            data_end = text_end - 1
            text_end = len(source)
        else:
            data_end = len(source)
            text_end = data_index - 1
    
    translated: Translated_data = process(code, text_start, text_end, data_start, data_end)
    with open(target_path, 'w+', encoding="utf-8") as file:
        if (len(translated.preload) != 0):
            file.write('preload:\n')
            for i in translated.preload:
                file.write(i.__str__() + '\n')
        file.write('program:\n')
        for i in translated.program:
            file.write(i.__str__() + '\n')

if __name__ == '__main__':
    assert len(sys.argv[1:]) == 2,  "Ожидаемый формат: translation.py <source_path> <target_path>"    
    main(sys.argv[1:])