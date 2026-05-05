#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from HuffNode import HuffNode
from PriorityQueue import PriorityQueue

freq = {"a":7, "b":1, "c":3, "d":4, "e":12, "f":1, "g":1, "h":1, "i":6, "j":0, 
        "k":0, "l":5, "m":3, "n":6, "o":5, "p":2, "q":0, "r":6, "s":6, "t":6, 
        "u":4, "v":1, "w":0, "x":0, "y":0, "z":0, "à":0, "é":2, "è":0, ",":2, 
        "-":0, ".":1, ";":0, "!":0, "?":0, "\n":0, "<sp>":15}

# ---------- construction de l'arbre ----------

def build_huffman_tree(freqs):
    pq = PriorityQueue()
    for ch, f in freqs.items():
        pq.push(HuffNode(ch, f), f)

    while True:
        if len(pq._queue) == 1:
            return pq.pop()
        n1 = pq.pop()
        n2 = pq.pop()
        parent = HuffNode(None, n1.freq + n2.freq, n1, n2)
        pq.push(parent, parent.freq)

# ---------- génération des codes ----------

def build_codes(node, prefix="", table=None):
    if table is None:
        table = {}
    if node.char is not None:
        table[node.char] = prefix
        return table
    if node.left:
        build_codes(node.left, prefix + "0", table)
    if node.right:
        build_codes(node.right, prefix + "1", table)
    return table

# ---------- encodage ----------

def encode_text(text, codes):
    bits = ""
    for c in text:
        if c == " ":
            c = "<sp>"
        if c in codes:
            bits += codes[c]
        else:
            # pour l’instant : on ignore les caractères inconnus
            # (on testera avec un texte simple)
            pass
    return bits

# ---------- décodage ----------

def decode_bits(bits, root):
    res = ""
    node = root
    for b in bits:
        if b == "0":
            node = node.left
        else:
            node = node.right
        if node.char is not None:
            if node.char == "<sp>":
                res += " "
            else:
                res += node.char
            node = root
    return res

# ---------- API encrypt / decrypt ----------

def encrypt(text):
    root = build_huffman_tree(freq)
    codes = build_codes(root)
    return encode_text(text, codes)

def decrypt(bits):
    root = build_huffman_tree(freq)
    return decode_bits(bits, root)

# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="Encrypt Decrypt and output files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encrypt", action="store_true")
    group.add_argument("-d", "--decrypt", action="store_true")
    
    parser.add_argument("input_path", type=str)
    parser.add_argument("-o", "--output", type=str, required=True)
    
    args = parser.parse_args()

    if args.encrypt:
        with open(args.input_path, 'r', encoding="utf-8") as f:
            text = f.read()
        encrypted_text = encrypt(text)
        with open(args.output, 'w', encoding="utf-8") as f:
            f.write(encrypted_text)

    elif args.decrypt:
        with open(args.input_path, 'r', encoding="utf-8") as f:
            bits = f.read().strip()
        decrypted_text = decrypt(bits)
        with open(args.output, 'w', encoding="utf-8") as f:
            f.write(decrypted_text)

if __name__ == "__main__":
    main()
