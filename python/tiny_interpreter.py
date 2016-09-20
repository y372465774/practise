#-*- coding:utf-8 -*-

class Interpreter:

    def __init__(self):
        self.stack = []
        self.enviroment = {}

    def STORE_NAME(self,name):
        val = self.stack.pop()
        self.enviroment[name] = val

    def LOAD_NAME(self,name):
        val = self.enviroment[name]
        self.stack.append(val)

    def LOAD_VALUE(self,number):
        self.stack.append(number)

    def PRINT_ANSWER(self):
        answer = self.stack.pop()
        print answer

    def ADD_TWO_VALUES(self):
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        total = first_num + second_num
        self.stack.append(total)

    def parse_argument(self,instruction,argument,what_to_execute):
        u""" 解析参数在不同指令中的含义"""
        numbers = ["LOAD_VALUE"]
        names = ["LOAD_NAME","STORE_NAME"]
        if instruction in numbers:
            argument = what_to_execute["numbers"][argument]
        elif instruction in names:
            argument = what_to_execute["names"][argument]
        return argument

    def run_code(self,what_to_execute):
        instructions = what_to_execute["instructions"]
        #numbers = what_to_execute["numbers"]
        for each_step in instructions:
            instruction,argument = each_step
            argument = self.parse_argument(instruction,argument,what_to_execute)
            
            bytecode_method = getattr(self,instruction)

            if argument is None:
                bytecode_method()
            else:
                bytecode_method(argument)
                
            #if instruction == "LOAD_VALUE":
            #    self.LOAD_VALUE(argument)
            #elif instruction == "ADD_TWO_VALUES":
            #    self.ADD_TWO_VALUES()
            #elif instruction == "PRINT_ANSWER":
            #    self.PRINT_ANSWER()

what_to_execute = {
    "instructions": [("LOAD_VALUE", 0),  # the first number
                     ("LOAD_VALUE", 1),  # the second number
                     ("ADD_TWO_VALUES", None),
                     ("PRINT_ANSWER", None)],
    "numbers": [7, 5] }

interpreter = Interpreter()
interpreter.run_code(what_to_execute)

what_to_execute = {
    "instructions": [("LOAD_VALUE", 0),
                     ("LOAD_VALUE", 1),
                     ("ADD_TWO_VALUES", None),
                     ("LOAD_VALUE", 2),
                     ("ADD_TWO_VALUES", None),
                     ("PRINT_ANSWER", None)],
    "numbers": [7, 5, 8] }

interpreter.run_code(what_to_execute)

what_to_execute = {
    "instructions": [("LOAD_VALUE", 0),
                     ("STORE_NAME", 0),
                     ("LOAD_VALUE", 1),
                     ("STORE_NAME", 1),
                     ("LOAD_NAME", 0),
                     ("LOAD_NAME", 1),
                     ("ADD_TWO_VALUES", None),
                     ("PRINT_ANSWER", None)],
    "numbers": [1, 2],
    "names":   ["a", "b"] }

interpreter.run_code(what_to_execute)
