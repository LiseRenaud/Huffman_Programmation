# -*- coding: utf-8 -*-
# la classe permet de représenter les nœuds de l'arbre de Huffman, 
# avec les attributs char (le caractère associé au nœud), 
# freq (la fréquence du caractère), 
# left (le nœud fils gauche) et right (le nœud fils droit). 
# La méthode __lt__ est définie pour permettre la comparaison des nœuds en fonction de leur fréquence, 
# ce qui est utile lors de la construction de l'arbre de Huffman.
class HuffNode:
    def __init__(self, char, freq, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq
