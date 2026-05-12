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
        parent = HuffNode(None, n1.freq + n2.freq, n1, n2)
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
def print_tree(node, indent="", is_left=True):
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
    bits = ""

    for c in text:
        if c == " ":
            c = "<sp>"

        if c in codes:
            bits += codes[c]
        else:
            bits += codes[ESC]

            for b in c.encode("utf-8"):
                bits += format(b, "08b")

    return bits


# =========================================================
# DÉCODAGE
# =========================================================
def decode_bits(bits, root):
    res = ""
    node = root

    i = 0
    while i < len(bits):
        node = node.left if bits[i] == "0" else node.right

        if node.char is not None:

            if node.char == "<sp>":
                res += " "

            elif node.char == ESC:
                byte_list = []
                i += 1

                while i < len(bits):
                    byte_list.append(int(bits[i:i+8], 2))
                    i += 8
                    try:
                        res += bytes(byte_list).decode("utf-8")
                        break
                    except:
                        continue

                node = root
                continue

            else:
                res += node.char

            node = root

        i += 1

    return res


# ici encrypt construit l'arbre de Huffman à partir de la able de fréquence, puis construit la table des codes à partir de l'arbre,
# puis on encode le texte a l'aide de la table des codes
def encrypt(text):
    root = build_huffman_tree(freq)
    codes = build_codes(root)
    return encode_text(text, codes), root


# ici decrypt reconstruit l'arbre depuis la table de fréquence puis on reconstruit le texte à partir des bits et de l'arbre
def decrypt(bits):
    root = build_huffman_tree(freq)
    return decode_bits(bits, root), root


def main():

    # Mise en place des arguments
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-e", "--encrypt", action="store_true")
    group.add_argument("-d", "--decrypt", action="store_true")

    parser.add_argument("input_path")
    parser.add_argument("-o", "--output", required=True)

    args = parser.parse_args()

    # Si l'option encrypt est choisie alors on lit le fichier d'entrée, puis on encode le texte et on lit le résultat du fichier de sortie
    if args.encrypt:
        #Lancement d'un timer
        start = time.time()

        with open(args.input_path, "r", encoding="utf-8") as f:
            text = f.read()

        bits, root = encrypt(text)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(bits)

        end = time.time()
        #Affichage du timer et de l'arbre final
        print("\n--- COMPRESSION TERMINÉE ---")
        print(f"Temps compression : {end - start:.4f} sec")

        print("\n===== ARBRE FINAL =====")
        print_tree(root)

    # Si l'option decrypt est choisie alors on lit le fichier d'entrée, puis on décode les bits et on lit le résultat du fichier de sortie
    elif args.decrypt:
        #Lancement d'un timer
        start = time.time()

        with open(args.input_path, "r", encoding="utf-8") as f:
            bits = f.read().strip()

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