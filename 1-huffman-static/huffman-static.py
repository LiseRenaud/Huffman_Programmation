#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
from HuffNode import HuffNode
from PriorityQueue import PriorityQueue

freq = {
    "a":7, "b":1, "c":3, "d":4, "e":12, "f":1, "g":1, "h":1, "i":6, "j":0,
    "k":0, "l":5, "m":3, "n":6, "o":5, "p":2, "q":0, "r":6, "s":6, "t":6,
    "u":4, "v":1, "w":0, "x":0, "y":0, "z":0,
    "à":0, "é":2, "è":0,
    ",":2, "-":0, ".":1, ";":0, "!":0, "?":0,
    "\n":0,
    "<sp>":15,
    "§ESC§": 1
}

ESC = "§ESC§"


# =========================================================
# ARBRE HUFFMAN
# =========================================================
def build_huffman_tree(freqs):
    pq = PriorityQueue()

    for ch, f in freqs.items():
        pq.push(HuffNode(ch, f), f)

    while len(pq._queue) > 1:
        n1 = pq.pop()
        n2 = pq.pop()

        parent = HuffNode(
            None,
            n1.freq + n2.freq,
            n1,
            n2
        )

        pq.push(parent, parent.freq)

    return pq.pop()


#construit la table de code à partir des fréquences de l'arbre de huffman
#on parcourt l'arbre de manière récursive et on ajoute 0 en allant dans les branches de gauche et 1 dans les branches de droite, 
#jusqu'à atteindre la fin d'une branche --> une feuille/un caractère auquel on associe le code binaire construit qu'on ajoute à notre table.
def build_codes(node, prefix="", table=None):

    if table is None:
        table = {}

    if node.char is not None:
        table[node.char] = prefix or "0"
        return table

    if node.left:
        build_codes(node.left, prefix + "0", table)

    if node.right:
        build_codes(node.right, prefix + "1", table)

    return table


# =========================================================
# AFFICHAGE ARBRE
# =========================================================
def print_tree(node, indent=""):

    if node is None:
        return

    prefix = "├── " if indent else ""

    if node.char is not None:

        label = node.char

        if label == "<sp>":
            label = "space"

        print(f"{indent}{prefix}'{label}' (freq={node.freq})")

    else:
        print(f"{indent}{prefix}* (freq={node.freq})")

    new_indent = indent + ("│   " if indent else "    ")

    print_tree(node.left, new_indent)
    print_tree(node.right, new_indent)


# On encode le texte caractère par caractère en utilisant les codes associés via la table des codes.
# si un caractère n'est pas dans la table alors on encode d'abord un caractère d'échappement puis on encode le caractère en binaire sur 8 bits et on ajoute 
def encode_text(text, codes):

    parts = []

    for c in text:

        if c == " ":
            c = "<sp>"

        if c in codes:
            parts.append(codes[c])

        else:
            # caractère inconnu
            parts.append(codes[ESC])

            for b in c.encode("utf-8"):
                parts.append(format(b, "08b"))

    return "".join(parts)


# =========================================================
# BITS -> TEXTE
# =========================================================
def decode_bits(bits, root):

    result = []
    node = root

    i = 0

    while i < len(bits):

        node = node.left if bits[i] == "0" else node.right

        if node.char is not None:

            # espace
            if node.char == "<sp>":
                result.append(" ")

            # caractère UTF-8 inconnu
            elif node.char == ESC:

                byte_list = []

                i += 1

                while i < len(bits):

                    chunk = bits[i:i+8]

                    if len(chunk) < 8:
                        break

                    byte_list.append(int(chunk, 2))
                    i += 8

                    try:
                        decoded = bytes(byte_list).decode("utf-8")
                        result.append(decoded)
                        break

                    except UnicodeDecodeError:
                        continue

                node = root
                continue

            else:
                result.append(node.char)

            node = root

        i += 1

    return "".join(result)


# =========================================================
# BITS -> OCTETS
# =========================================================
def bits_to_bytes(bits):

    padding = (8 - len(bits) % 8) % 8

    bits += "0" * padding

    data = bytearray()

    for i in range(0, len(bits), 8):

        byte = bits[i:i+8]
        data.append(int(byte, 2))

    # premier octet = padding
    return bytes([padding]) + bytes(data)


# =========================================================
# OCTETS -> BITS
# =========================================================
def bytes_to_bits(data):

    padding = data[0]
    data = data[1:]

    parts = []

    for b in data:
        parts.append(format(b, "08b"))

    bits = "".join(parts)

    if padding:
        bits = bits[:-padding]

    return bits


# ici encrypt construit l'arbre de Huffman à partir de la able de fréquence, puis construit la table des codes à partir de l'arbre,
# puis on encode le texte a l'aide de la table des codes
def encrypt(text):
    root = build_huffman_tree(freq)
    codes = build_codes(root)
    bits = encode_text(text, codes)
    return bits, root


# ici decrypt reconstruit l'arbre depuis la table de fréquence puis on reconstruit le texte à partir des bits et de l'arbre
def decrypt(bits):
    root = build_huffman_tree(freq)
    text = decode_bits(bits, root)
    return text, root


def main():

    # Mise en place des arguments
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-e","--encrypt",action="store_true")
    group.add_argument("-d","--decrypt",action="store_true")
    
    parser.add_argument("input_path")
    parser.add_argument("-o","--output",required=True)

    args = parser.parse_args()

    # Si l'option encrypt est choisie alors on lit le fichier d'entrée, puis on encode le texte et on lit le résultat du fichier de sortie
    if args.encrypt:
        #Lancement d'un timer
        start = time.time()

        with open(args.input_path, "r", encoding="utf-8") as f:
            text = f.read()

        bits, root = encrypt(text)

        binary_data = bits_to_bytes(bits)

        with open(args.output, "wb") as f:
            f.write(binary_data)

        end = time.time()
        #Affichage du timer et de l'arbre final
        print("\n--- COMPRESSION TERMINÉE ---")
        print(f"Temps compression : {end - start:.4f} sec")

        original_size = len(text.encode("utf-8"))
        compressed_size = len(binary_data)

        ratio = compressed_size / original_size * 100

        print(f"Taille originale : {original_size} octets")
        print(f"Taille compressée : {compressed_size} octets")
        print(f"Ratio : {100-ratio:.2f}%")

        print("\n===== ARBRE FINAL =====")
        print_tree(root)

    # Si l'option decrypt est choisie alors on lit le fichier d'entrée, puis on décode les bits et on lit le résultat du fichier de sortie
    elif args.decrypt:
        #Lancement d'un timer
        start = time.time()

        with open(args.input_path, "rb") as f:
            binary_data = f.read()

        bits = bytes_to_bits(binary_data)

        text, root = decrypt(bits)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)

        end = time.time()

        #Affichage du timer et de l'arbre reconstruit
        print("\n--- DÉCOMPRESSION TERMINÉE ---")
        print(f"Temps décompression : {end - start:.4f} sec")

        print("\n===== ARBRE RECONSTRUIT =====")
        print_tree(root)


if __name__ == "__main__":
    main()