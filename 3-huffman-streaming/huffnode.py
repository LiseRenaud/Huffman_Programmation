class HuffNode:
    def __init__(self, char=None, weight=0, parent=None, order=0):
        self.char = char
        self.weight = weight
        self.parent = parent
        self.left = None
        self.right = None
        self.order = order

    def is_leaf(self):
        return self.left is None and self.right is None