#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import socket
import time
from collections import defaultdict


# =========================================================
# CONFIG DEMO
# =========================================================

DISPLAY_EVERY = 50     # affichage arbre tous les X caractères
SLEEP_TIME = 0.0001      # ralentissement volontaire


# =========================================================
# NODE
# =========================================================

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


# =========================================================
# ADAPTIVE HUFFMAN FGK
# =========================================================

class AdaptiveHuffman:
    def __init__(self):

        self.max_order = 512

        self.root = Node(order=self.max_order)

        self.NYT = self.root

        self.nodes = {}

        self.blocks = defaultdict(set)

        self.blocks[0].add(self.root)

    # -----------------------------------------------------

    def get_code(self, node):

        code = []

        while node.parent:

            if node.parent.left == node:
                code.append("0")
            else:
                code.append("1")

            node = node.parent

        return "".join(reversed(code))

    # -----------------------------------------------------

    def update_blocks(self, node, old_weight, new_weight):

        if node in self.blocks[old_weight]:
            self.blocks[old_weight].remove(node)

        self.blocks[new_weight].add(node)

    # -----------------------------------------------------

    def find_highest_in_block(self, weight):

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

            highest = self.find_highest_in_block(node.weight)

            if highest and highest != node and highest != node.parent:
                self.swap(node, highest)

            node.weight += 1

            self.update_blocks(node, old_weight, node.weight)

            node = node.parent

    # -----------------------------------------------------

    def add_new_symbol(self, symbol):

        new_internal = Node(weight=0, order=self.NYT.order)

        new_leaf = Node(
            symbol=symbol,
            weight=0,
            order=self.NYT.order - 1
        )

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


# =========================================================
# AFFICHAGE ARBRE
# =========================================================

def print_tree(node, prefix="", is_left=True):

    if node is None:
        return

    connector = "├── " if is_left else "└── "

    if node.symbol is None:

        label = f"INT/NYT (w={node.weight}, ord={node.order})"

    else:

        try:
            ch = chr(node.symbol)
            label = f"'{ch}' ({node.symbol})"
        except:
            label = str(node.symbol)

        label += f" [w={node.weight}, ord={node.order}]"

    print(prefix + connector + label)

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


# =========================================================
# PRODUCTEUR
# =========================================================

def producer(input_path):

    HOST = "0.0.0.0"
    PORT = 5000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))

    server.listen(1)

    local_ip = socket.gethostbyname(socket.gethostname())

    print("\n===== PRODUCTEUR =====")
    print(f"Adresse IP : {local_ip}")
    print(f"Port : {PORT}")

    print("\nEn attente du consommateur...\n")

    conn, addr = server.accept()

    print(f"Connexion reçue depuis {addr}")

    with open(input_path, "rb") as f:
        data = f.read()

    tree = AdaptiveHuffman()

    counter = 0

    start = time.perf_counter()

    # -----------------------------------------------------
    # ENVOI STREAMING
    # -----------------------------------------------------

    for byte in data:

        if byte in tree.nodes:

            node = tree.nodes[byte]

            bits = tree.get_code(node)

        else:

            bits = tree.get_code(tree.NYT)

            bits += f"{byte:08b}"

            node = tree.add_new_symbol(byte)

        tree.update(node)

        conn.sendall(bits.encode())

        counter += 1

        # affichage périodique
        if counter % DISPLAY_EVERY == 0:

            print(f"\n[PRODUCTEUR] {counter} caractères envoyés")

            print("[PRODUCTEUR] arbre actuel :")

            print_tree(tree.root)

            print("\n-----------------------------------\n")

        time.sleep(SLEEP_TIME)

    conn.sendall(b"EOF")

    end = time.perf_counter()

    print("\n===== FIN PRODUCTEUR =====")
    print(f"Temps total : {end - start:.4f} secondes")

    conn.close()
    server.close()


# =========================================================
# CONSOMMATEUR
# =========================================================

def consumer(ip_port):

    ip, port = ip_port.split(":")

    port = int(port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("\nConnexion au producteur...")

    sock.connect((ip, port))

    print("Connecté.\n")

    tree = AdaptiveHuffman()

    bits_buffer = ""

    output = []

    counter = 0

    start = time.perf_counter()

    while True:

        data = sock.recv(1024)

        if not data:
            break

        eof = False

        if b"EOF" in data:

            data = data.replace(b"EOF", b"")

            eof = True

        bits_buffer += data.decode()

        i = 0

        while i < len(bits_buffer):

            node = tree.root

            # descente arbre
            while not node.is_leaf():

                if i >= len(bits_buffer):
                    break

                bit = bits_buffer[i]

                i += 1

                if bit == "0":
                    node = node.left
                else:
                    node = node.right

            else:

                if node == tree.NYT:

                    if i + 8 > len(bits_buffer):
                        break

                    byte = int(bits_buffer[i:i + 8], 2)

                    i += 8

                    output.append(byte)

                    node = tree.add_new_symbol(byte)

                else:

                    output.append(node.symbol)

                tree.update(node)

                counter += 1

                # affichage périodique
                if counter % DISPLAY_EVERY == 0:

                    print(f"\n[CONSOMMATEUR] {counter} caractères reçus")

                    print("[CONSOMMATEUR] arbre actuel :")

                    print_tree(tree.root)

                    print("\n-----------------------------------\n")

        bits_buffer = bits_buffer[i:]

        if eof:
            break

    end = time.perf_counter()

    text = bytes(output).decode("utf-8")

    print("\n===== TEXTE RECONSTRUIT =====\n")

    print(text)

    print("\n===== FIN CONSOMMATEUR =====")

    print(f"Temps total : {end - start:.4f} secondes")

    sock.close()


# =========================================================
# CLI
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description="Huffman Streaming Demo"
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-p",
        "--producer",
        metavar="FILE"
    )

    group.add_argument(
        "-c",
        "--consumer",
        metavar="IP:PORT"
    )

    args = parser.parse_args()

    if args.producer:
        producer(args.producer)

    elif args.consumer:
        consumer(args.consumer)


if __name__ == "__main__":
    main()