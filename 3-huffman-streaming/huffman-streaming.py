#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

# ---------------------------------------------------------
# Node
# ---------------------------------------------------------

class Node:
    def __init__(self, char=None, weight=0, parent=None, order=0):
        self.char = char
        self.weight = weight
        self.parent = parent
        self.left = None
        self.right = None
        self.order = order  # important pour FGK

    def is_leaf(self):
        return self.left is None and self.right is None


# ---------------------------------------------------------
# Adaptive Huffman (FGK)
# ---------------------------------------------------------

class AdaptiveHuffman:
    def __init__(self):
        self.max_order = 512
        self.root = Node(order=self.max_order)
        self.NYT = self.root
        self.nodes = {}  # char -> node

    # ---------------------------------
    def get_code(self, node):
        code = ""
        while node.parent:
            if node.parent.left == node:
                code = "0" + code
            else:
                code = "1" + code
            node = node.parent
        return code

    # ---------------------------------
    def find_highest_node(self, weight):
        result = None

        def traverse(node):
            nonlocal result
            if node is None:
                return
            if node.weight == weight:
                if result is None or node.order > result.order:
                    result = node
            traverse(node.left)
            traverse(node.right)

        traverse(self.root)
        return result

    # ---------------------------------
    def swap(self, n1, n2):
        if n1 == n2 or n1.parent == n2 or n2.parent == n1:
            return

        p1, p2 = n1.parent, n2.parent

        if p1.left == n1:
            p1.left = n2
        else:
            p1.right = n2

        if p2.left == n2:
            p2.left = n1
        else:
            p2.right = n1

        n1.parent, n2.parent = p2, p1
        n1.order, n2.order = n2.order, n1.order

    # ---------------------------------
    def update(self, node):
        while node:
            highest = self.find_highest_node(node.weight)
            if highest and highest != node and highest != node.parent:
                self.swap(node, highest)

            node.weight += 1
            node = node.parent

    # ---------------------------------
    def add_new_char(self, char):
        new_internal = Node(weight=0, order=self.NYT.order)
        new_leaf = Node(char=char, weight=0, order=self.NYT.order - 1)

        new_internal.left = self.NYT
        new_internal.right = new_leaf

        new_internal.parent = self.NYT.parent

        if self.NYT.parent:
            if self.NYT.parent.left == self.NYT:
                self.NYT.parent.left = new_internal
            else:
                self.NYT.parent.right = new_internal
        else:
            self.root = new_internal

        self.NYT.parent = new_internal
        new_leaf.parent = new_internal

        self.nodes[char] = new_leaf
        self.NYT.order -= 2

        return new_leaf


# ---------------------------------------------------------
# Compression
# ---------------------------------------------------------

def encrypt(text):
    tree = AdaptiveHuffman()
    bits = ""

    for char in text:
        if char in tree.nodes:
            node = tree.nodes[char]
            bits += tree.get_code(node)
        else:
            bits += tree.get_code(tree.NYT)
            bits += f"{ord(char):08b}"
            node = tree.add_new_char(char)

        tree.update(node)

    # padding
    padding = (8 - len(bits) % 8) % 8
    bits += "0" * padding

    # ajouter 8 bits au début pour stocker padding
    header = f"{padding:08b}"
    bits = header + bits

    return int(bits, 2).to_bytes(len(bits) // 8, "big")


# ---------------------------------------------------------
# Décompression
# ---------------------------------------------------------

def decrypt(data):
    bits = "".join(f"{b:08b}" for b in data)

    # lire padding
    padding = int(bits[:8], 2)
    bits = bits[8:]

    # retirer bits inutiles à la fin
    if padding > 0:
        bits = bits[:-padding]

    tree = AdaptiveHuffman()
    result = ""

    i = 0
    while i < len(bits):
        node = tree.root

        # descendre dans l'arbre
        while not node.is_leaf():
            if i >= len(bits):
                return result
            bit = bits[i]
            i += 1
            node = node.left if bit == "0" else node.right

        if node == tree.NYT:
            if i + 8 > len(bits):
                break
            char = chr(int(bits[i:i+8], 2))
            i += 8
            result += char
            node = tree.add_new_char(char)
        else:
            result += node.char

        tree.update(node)

    return result


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Huffman Streaming (Adaptive)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encrypt", action="store_true")
    group.add_argument("-d", "--decrypt", action="store_true")

    parser.add_argument("input_path", type=str)
    parser.add_argument("-o", "--output", type=str, required=True)

    args = parser.parse_args()

    if args.encrypt:
        with open(args.input_path, "r", encoding="utf-8") as f:
            text = f.read()
        data = encrypt(text)
        with open(args.output, "wb") as f:
            f.write(data)

    elif args.decrypt:
        with open(args.input_path, "rb") as f:
            data = f.read()
        text = decrypt(data)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()