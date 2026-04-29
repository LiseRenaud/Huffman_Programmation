class HuffNode:
    def __init__(self, char=None, frequency=0):
        self.myChar = char
        self.myFrequency = frequency
        self.myLeft = None
        self.myRight = None