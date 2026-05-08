#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from collections import defaultdict
import time

# ---------------------------------------------------------
# Node
# ---------------------------------------------------------

class Node:
    def __init__(self, symbol=None, weight=0, parent=None, order=0):
        self.symbol = symbol
        self.weight = weight
        self.parent = parent
        self.left = None
        self.right = None
        self.order = order

    def is_leaf(self):
        return self.left is None and self.right is None


# ---------------------------------------------------------
# Adaptive Huffman FGK optimisé
# ---------------------------------------------------------

class AdaptiveHuffman:
    def __init__(self):
        self.max_order = 512
        self.root = Node(order=self.max_order)
        self.NYT = self.root
        self.nodes = {}

        # 🔥 OPTIMISATION MAJEURE : blocs par poids
        self.blocks = defaultdict(set)

        self.blocks[0].add(self.root)

    # -----------------------------------------------------
    def get_code(self, node):
        code = []
        while node.parent:
            code.append("0" if node.parent.left == node else "1")
            node = node.parent
        return "".join(reversed(code))

    # -----------------------------------------------------
    def update_blocks(self, node, old_weight, new_weight):
        if node in self.blocks[old_weight]:
            self.blocks[old_weight].remove(node)
        self.blocks[new_weight].add(node)

    # -----------------------------------------------------
    def find_highest_in_block(self, weight):
        # prend le node avec ordre max dans le bloc
        return max(self.blocks[weight], key=lambda n: n.order)

    # -----------------------------------------------------
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

    # -----------------------------------------------------
    def update(self, node):
        while node:
            old_weight = node.weight

            # 🔥 O(1) amorti lookup
            highest = self.find_highest_in_block(node.weight)

            if highest and highest != node and highest != node.parent:
                self.swap(node, highest)

            node.weight += 1

            # mise à jour des blocs
            self.update_blocks(node, old_weight, node.weight)

            node = node.parent

    # -----------------------------------------------------
    def add_new_symbol(self, symbol):
        new_internal = Node(weight=0, order=self.NYT.order)
        new_leaf = Node(symbol=symbol, weight=0, order=self.NYT.order - 1)

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

        self.nodes[symbol] = new_leaf

        # blocs
        self.blocks[0].add(new_internal)
        self.blocks[0].add(new_leaf)

        self.NYT.order -= 2

        return new_leaf


# ---------------------------------------------------------
# Compression
# ---------------------------------------------------------

def encrypt(text):
    data = text.encode("utf-8")

    tree = AdaptiveHuffman()
    bits = []

    for byte in data:
        if byte in tree.nodes:
            node = tree.nodes[byte]
            bits.append(tree.get_code(node))
        else:
            bits.append(tree.get_code(tree.NYT))
            bits.append(f"{byte:08b}")
            node = tree.add_new_symbol(byte)

        tree.update(node)

    bits = "".join(bits)

    padding = (8 - len(bits) % 8) % 8
    bits += "0" * padding

    header = f"{padding:08b}"
    bits = header + bits

    return int(bits, 2).to_bytes(len(bits) // 8, "big")


# ---------------------------------------------------------
# Décompression
# ---------------------------------------------------------

def decrypt(data):
    bits = "".join(f"{b:08b}" for b in data)

    padding = int(bits[:8], 2)
    bits = bits[8:]

    if padding:
        bits = bits[:-padding]

    tree = AdaptiveHuffman()
    result_bytes = []

    i = 0

    while i < len(bits):
        node = tree.root

        while not node.is_leaf():
            bit = bits[i]
            i += 1
            node = node.left if bit == "0" else node.right

        if node == tree.NYT:
            byte = int(bits[i:i+8], 2)
            i += 8
            result_bytes.append(byte)
            node = tree.add_new_symbol(byte)
        else:
            result_bytes.append(node.symbol)

        tree.update(node)

    return bytes(result_bytes).decode("utf-8")


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Optimized Huffman Streaming (FGK)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encrypt", action="store_true")
    group.add_argument("-d", "--decrypt", action="store_true")

    parser.add_argument("input_path")
    parser.add_argument("-o", "--output", required=True)

    args = parser.parse_args()

    start_time = time.perf_counter()  # ⏱️ début chrono

    if args.encrypt:
        with open(args.input_path, "r", encoding="utf-8") as f:
            text = f.read()

        data = encrypt(text)

        with open(args.output, "wb") as f:
            f.write(data)

        mode = "Compression"

    else:
        with open(args.input_path, "rb") as f:
            data = f.read()

        text = decrypt(data)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)

        mode = "Décompression"

    end_time = time.perf_counter()  # ⏱️ fin chrono

    print(f"\n--- {mode} terminée ---")
    print(f"Temps d'exécution : {end_time - start_time:.4f} secondes")


if __name__ == "__main__":
    main()