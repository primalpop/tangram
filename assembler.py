#!/usr/bin/env python

import sys
import re

#Assembler for Hack

class SymbolTable:
    #Keeps a correspondence between symbolic labels and numeric Addresses
    def __init__(self):
        self.symbol_table = {"SP" : 0, "LCL" : 1, "ARG" : 2, "THIS" : 3, 
                   "THAT" : 4, "SCREEN" : 16384, "KBD" : 24576, 
                    "R0" : 0, "R1" : 1, "R2" : 2, "R3" : 3, 
                    "R4" : 4, "R5" : 5, "R6" : 6, "R7" : 7, "R8" : 8, 
                    "R9" : 9, "R10" : 10, "R11" : 11, "R12" : 12, 
                    "R13" : 13, "R14" : 14, "R15" : 15}
    
    def addEntry(self, symbol, address):
        self.symbol_table[symbol] = address 
                
    def contains(self, symbol):    
        if symbol in self.symbol_table:
            return True
        else:
            return False

    def GetAddress(self, symbol):
        return self.symbol_table[symbol]    

class Parser:
    #Parser module
    #Parses and returns the components
    def __init__(self, filePointer): 
        str = filePointer.read()
        lines = str.split('\n')
        cmds = []
        for l in lines:
            com = self.stripper(l)
            if com != '':
                if com[0] == "/":
                    continue
                else:
                    cmds.append(com) 
                     
        self.commands = cmds[:]
        self.commands.reverse()
        self.backup = self.commands[:]
    
    def stripper(self, string):
        c = string.replace(' ', '')
        c = c.replace('\t', '') 
        c = c.replace('\r','')
        return re.sub(r'//.*', '', c)
        
    def refillList(self):
        self.commands = self.backup[:]
                   
    def hasMoreCommands(self):
        if len(self.commands)>0:
            return True
        else:
            return False

    def advance(self):
        self.curcmd = self.commands.pop()
            
    def commandType(self):
        if re.search(r'@\w+', self.curcmd):
            return "A_COMMAND"
        elif self.curcmd.find('(') >= 0:
            return "L_COMMAND"
        elif self.curcmd.find('=') >=0 :
            return "C_COMMAND"
        elif self.curcmd.find(';') >=0:
            return "C_COMMAND"
    
    def symbol(self):
        match = re.search(r'\w+.*', self.curcmd)
        return match.group()
    
    def dest(self):
        self.eq_index = self.curcmd.find('=')
        if self.eq_index > 0:
            str = self.curcmd[:self.eq_index]
            self.dest_flag=1
            return str
        else:
            self.dest_flag=0
            return ''
        
    def comp(self):
        self.sem_index = self.curcmd.find(';')
        if self.sem_index > 0:
            return self.curcmd[self.eq_index+1:self.sem_index]
        else:
            return self.curcmd[self.eq_index+1:]    
    
    def jump(self):
        if self.sem_index > 0:
            self.jump_flag = 1
            return self.curcmd[self.sem_index+1:]
        else:
            self.jump_flag = 0
            return ' '
        
class Code_Module:
    #Translates assembly language mnemonics to binary code
    azcomp = {"0" : "101010", "1" : "111111", "-1" : "111010", 
            "D" : "001100", "A" : "110000", "!D" : "001101", "!A" : "110001", 
            "-D" : "001111", "-A" : "110011", "D+1" : "011111", "A+1" : "110111", 
            "D-1" : "001110", "A-1" : "110010", "D+A" : "000010", "D-A" : "010011", 
            "A-D" : "000111", "D&A" : "000000", "D|A" : "010101"}
            
    aocomp = {"M" : "110000", "!M" : "110001", "-M" : "110011", "M+1" : "110111",
                    "M-1" : "110010", "D+M" : "000010", "D-M" : "010011", 
                    "M-D" : "000111", "D&M" : "000000", "D|M" : "010101"} 
    dest = {"M" : "001", "D" : "010", "MD" : "011", "A" : "100", 
                "AM" : "101", "AD" : "110", "AMD" : "111", "0" : "000"}

    jump = {"JGT" : "001", "JEQ" : "010", "JGE" : "011", "JLT" : "100", 
                "JNE" : "101", "JLE" : "110", "JMP" : "111", "0" : "000"}
    
    
    def dest_code(self, destmnem):  
        return self.dest[destmnem]
    
    def comp_code(self, compmnem):    
        if compmnem.find('M') != -1 :
            self.avalue = 1
            return self.aocomp[compmnem]
        else:
            self.avalue = 0
            return self.azcomp[compmnem]  
                
    def jump_code(self, jumpmnem):
        return self.jump[jumpmnem]
        
        
def main():
    
    f = open(sys.argv[1], 'r')
    output = sys.argv[1].replace('asm', 'hack')
    o = open(output, 'w')
    
    pass_count = 1 #Denotes whether first or second pass   
    instr_count = 0 #Denotes ROM Address
    addr_avail = 15 #Denotes next available RAM address ; Starts from 16 after storing pre-defined symbols
    
    sixt = ['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0'] #sixteen bit place-holder for symbols
    
    mParse = Parser(f)
    #print mParse.commands
    Coder = Code_Module()
    symTab = SymbolTable()
    
    
    while pass_count < 3:
        mParse.refillList()
        while mParse.hasMoreCommands():
            #print "has got more"
            mParse.advance()
            #print mParse.curcmd
            type = mParse.commandType()
            if pass_count == 2:    
                #In pass 2 A_COMMAND and C_COMMAND are handled
                if type == "A_COMMAND":
                    symb_mnem = mParse.symbol()
                    #print symb_mnem
                    if symb_mnem.isdigit():
                        binary_code = convert_to_bin(symb_mnem, sixt)
                    else:
                        if symTab.contains(symb_mnem):
                            #Symbol already in Symbol Table
                            address = symTab.GetAddress(symb_mnem)
                            print symb_mnem, address
                            binary_code = convert_to_bin(address, sixt)
                            
                        else:
                            #Adding symbol to Symbol Table
                            addr_avail = addr_avail + 1
                            symTab.addEntry(symb_mnem, addr_avail)
                            print symb_mnem, addr_avail
                            binary_code = convert_to_bin(addr_avail, sixt)
                    o.write(binary_code + "\n")    #writes binary code to file        
                elif type == "C_COMMAND":
                    dest_mnem = mParse.dest()
                    #print dest_mnem 
                    if mParse.dest_flag :
                        dest_bin = Coder.dest_code(dest_mnem)
                    else:
                        dest_bin = '000'       
                        #print dest_bin
                    comp_mnem = mParse.comp()
                    comp_bin = Coder.comp_code(comp_mnem)
                    #print comp_mnem, comp_bin
                    jump_mnem = mParse.jump()
                    if mParse.jump_flag:
                        jump_bin = Coder.jump_code(jump_mnem)
                    else:
                        jump_bin = '000'    
                    #print jump_mnem, jump_bin
                    binary_code = '111' + str(Coder.avalue) + comp_bin + dest_bin + jump_bin
                    #print binary_code 
                    o.write(binary_code + "\n")    #writes binary code to file
            else:
                #Pass 1
                if type == "L_COMMAND":
                    #Labels are added to Symbol Table with address of next command
                    length = len(mParse.curcmd)     
                    symbol = mParse.curcmd[1:length-1]
                    symTab.addEntry(symbol, instr_count)
                    print symbol, instr_count
                    
                else: 
                    #In Pass 1, the instruction count is increased for A or C command
                    instr_count = instr_count + 1    
        pass_count = pass_count + 1    
           
        
def convert_to_bin(dec_str, sixt):
    #Converts Decimal string to 16 bit binary
    n = int(dec_str)
    bstr = ''
    while n > 0:
        bstr = str(n % 2) + bstr
        n = n >> 1
    list = []
    for k in sixt:
        list.append(k)
    length = len(bstr)
    l = 16 - length
    list [l:] = bstr
    s = ''
    string = s.join(list)
    return string       
    
if __name__ == '__main__':
    main()        