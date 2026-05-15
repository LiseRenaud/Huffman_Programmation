#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from collections import defaultdict
import time


# classe noeud pour arbre huffman adaptatif, 
# avec symboles, 
# poids,
# liens parent-enfant et ordre pour la gestion des blocs de poids.
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


# Cette classe implémente l'algorithme de Huffman adaptatif,
# avec une optimisation basée sur la gestion de blocs de poids pour accélérer les opérations de mise à jour de l'arbre.
class AdaptiveHuffman:
    def __init__(self):
        self.max_order = 512
        self.root = Node(order=self.max_order)
        self.NYT = self.root
        self.nodes = {}

        # optimisation : blocs par poids
        self.blocks = defaultdict(set)

        self.blocks[0].add(self.root)

    # obtenir le code binaire d'un noeud en remontant vers la racine
    def get_code(self, node):
        code = []

        while node.parent:
            if node.parent.left == node:
                code.append("0")
            else:
                code.append("1")

            node = node.parent

        return "".join(reversed(code))

    # mise à jour des blocs de poids lors de l'incrémentation du poids d'un noeud
    def update_blocks(self, node, old_weight, new_weight):
        if node in self.blocks[old_weight]:
            self.blocks[old_weight].remove(node)

        self.blocks[new_weight].add(node)

    # trouver le nœud le plus élevé dans un bloc de poids donné
    def find_highest_in_block(self, weight):
        return max(self.blocks[weight], key=lambda n: n.order)

    # échanger deux nœuds dans l'arbre
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

    # mise à jour de l'arbre après l'ajout d'un symbole ou l'incrémentation du poids d'un nœud,
    # en utilisant les blocs de poids pour trouver rapidement les nœuds à échanger.
    def update(self, node):
        while node:
            old_weight = node.weight

            highest = self.find_highest_in_block(node.weight)

            if highest and highest != node and highest != node.parent:
                self.swap(node, highest)

            node.weight += 1

            self.update_blocks(node, old_weight, node.weight)

            node = node.parent

    # ajout d'un nouveau symbole à l'arbre en créant un nouveau nœud interne et une nouvelle feuille pour le symbole,
    # et en mettant à jour les liens parent-enfant et les blocs de poids.
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

        self.blocks[0].add(new_internal)
        self.blocks[0].add(new_leaf)

        self.NYT.order -= 2

        return new_leaf


# affichage de l'arbre de huffman de manière structurée, avec des symboles lisibles et les poids associés à chaque nœud.
def print_tree(node, prefix="", is_left=True):
    if node is None:
        return

    connector = "├── " if is_left else "└── "

    if node.symbol is None:
        label = f"NYT/INT (w={node.weight}, ord={node.order})"
    else:
        try:
            ch = chr(node.symbol)
            label = f"'{ch}' ({node.symbol})"
        except:
            label = str(node.symbol)

        label += f" [w={node.weight}, ord={node.order}]"

    print(prefix + connector + label)

    if node.left or node.right:

        if node.left:
            print_tree(
                node.left,
                prefix + ("│   " if is_left else "    "),
                True
            )

        if node.right:
            print_tree(
                node.right,
                prefix + ("│   " if is_left else "    "),
                False
            )


# la fonction de compression lit le texte d'entrée, 
# encode chaque caractère en utilisant l'arbre de Huffman adaptatif,
# et construit une chaîne de bits représentant le texte compressé, 
# en ajoutant un en-tête pour le padding 
# et en convertissant la chaîne de bits en bytes pour l'écriture dans un fichier binaire.
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

    compressed = int(bits, 2).to_bytes(len(bits) // 8, "big")

    return compressed, tree

# fonction de décompression on lit les données compressées, puis on reconstruit l'arbre de Huffman adaptatif en parcourant les bits de la chaîne compressée,
# on décode chaque symbole en suivant les chemins dans l'arbre,
# et on reconstruit le texte original à partir des symboles décodés, 
# en gérant le padding et en convertissant les bytes en texte UTF-8.
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

            if bit == "0":
                node = node.left
            else:
                node = node.right

        if node == tree.NYT:

            byte = int(bits[i:i + 8], 2)
            i += 8

            result_bytes.append(byte)

            node = tree.add_new_symbol(byte)

        else:
            result_bytes.append(node.symbol)

        tree.update(node)

    text = bytes(result_bytes).decode("utf-8")

    return text, tree


def main():
    parser = argparse.ArgumentParser(
        description="Optimized Huffman Streaming (FGK)"
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-e", "--encrypt", action="store_true")
    group.add_argument("-d", "--decrypt", action="store_true")

    parser.add_argument("input_path")

    parser.add_argument(
        "-o",
        "--output",
        required=True
    )

    args = parser.parse_args()

    # début du timer

    start_time = time.perf_counter()

    # si les arguments indiquent une compression, on lit le texte d'entrée, 
    # on encode chaque caractère en utilisant l'arbre de Huffman adaptatif,
    # et on construit une chaîne de bits représentant le texte compressé, 
    # en ajoutant un en-tête pour le padding et en convertissant la chaîne de bits en bytes pour l'écriture dans un fichier binaire.
    if args.encrypt:

        with open(args.input_path, "r", encoding="utf-8") as f:
            text = f.read()

        data, tree = encrypt(text)

        with open(args.output, "wb") as f:
            f.write(data)

        mode = "Compression"

    # si les arguments indique une décompression, on lit les données compressées,
    # puis on reconstruit l'arbre de Huffman adaptatif en parcourant les bits de la chaîne compressée, 
    # on décode chaque symbole en suivant les chemins dans l'arbre,
    # et on reconstruit le texte original à partir des symboles décodés, 
    # en gérant le padding et en convertissant les bytes en texte UTF-8, avant de l'écrire dans un fichier texte.

    else:

        with open(args.input_path, "rb") as f:
            data = f.read()

        text, tree = decrypt(data)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)

        mode = "Décompression"

    # fin du timer

    end_time = time.perf_counter()

    # temps d'exécution et affichage du mode (compression ou décompression)

    print(f"\n--- {mode} terminée ---")
    print(f"Temps d'exécution : {end_time - start_time:.4f} secondes")

    # affichage de l'arbre de huffman final

    if args.encrypt:
        print("\n===== ARBRE FINAL APRES COMPRESSION =====")
    else:
        print("\n===== ARBRE FINAL APRES DECOMPRESSION =====")

    print_tree(tree.root)


if __name__ == "__main__":
    main()