class SymbolTable:
    def __init__(self):
        self.table = {}

    def add(self, name, datatype):
        self.table[name] = datatype

    def get_all(self):
        return self.table