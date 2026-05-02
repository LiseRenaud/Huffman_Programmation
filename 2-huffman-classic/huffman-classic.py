#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from huffnode import HuffNode
from priorityqueue import PriorityQueue

# ---------------------------------------------------------
# 1. Construire l'arbre de Huffman
# ---------------------------------------------------------

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

# ---------------------------------------------------------
# 2. Générer les codes
# ---------------------------------------------------------

def build_codes(node, prefix="", table=None):
    if table is None:
        table = {}
    if node.char is not None:
        table[node.char] = prefix
        return table
    build_codes(node.left, prefix + "0", table)
    build_codes(node.right, prefix + "1", table)
    return table

# ---------------------------------------------------------
# 3. Sérialisation BINAIRE de l'arbre
# ---------------------------------------------------------
# Format :
#   1 + 8 bits du caractère  → feuille
#   0 + gauche + droite      → nœud interne
# ---------------------------------------------------------

def serialize_tree(node):
    if node.char is not None:
        return "1" + f"{ord(node.char):08b}"
    return "0" + serialize_tree(node.left) + serialize_tree(node.right)

# ---------------------------------------------------------
# 4. Désérialisation BINAIRE
# ---------------------------------------------------------

def deserialize_tree(bits, index=0):
    if bits[index] == "1":
        char_bits = bits[index+1:index+9]
        char = chr(int(char_bits, 2))
        return HuffNode(char, 0), index + 9
    else:
        left, i = deserialize_tree(bits, index + 1)
        right, j = deserialize_tree(bits, i)
        return HuffNode(None, 0, left, right), j

# ---------------------------------------------------------
# 5. Encoder le texte
# ---------------------------------------------------------

def encode_text(text, codes):
    return "".join(codes[c] for c in text)

# ---------------------------------------------------------
# 6. Décoder les bits
# ---------------------------------------------------------

def decode_bits(bits, root):
    res = ""
    node = root
    for b in bits:
        node = node.left if b == "0" else node.right
        if node.char is not None:
            res += node.char
            node = root
    return res

# ---------------------------------------------------------
# 7. Compression
# ---------------------------------------------------------

def encrypt(text):
    # 1. compter les fréquences
    freqs = {}
    for c in text:
        freqs[c] = freqs.get(c, 0) + 1

    # 2. construire l'arbre
    root = build_huffman_tree(freqs)

    # 3. générer les codes
    codes = build_codes(root)

    # 4. sérialiser l'arbre
    tree_serialized = serialize_tree(root)
    tree_size = len(tree_serialized)

    # 5. encoder le texte
    bits = encode_text(text, codes)

    # 6. assembler : taille arbre (32 bits) + arbre + bits
    header = f"{tree_size:032b}"
    full = header + tree_serialized + bits

    # 7. padding pour aligner sur 8 bits
    padding = (8 - len(full) % 8) % 8
    full += "0" * padding

    # 8. conversion en bytes
    data = int(full, 2).to_bytes(len(full) // 8, "big")
    return data

# ---------------------------------------------------------
# 8. Décompression
# ---------------------------------------------------------

def decrypt(data):
    # convertir bytes → bits
    bits = "".join(f"{byte:08b}" for byte in data)

    # lire taille arbre
    tree_size = int(bits[:32], 2)

    # lire arbre
    tree_data = bits[32:32 + tree_size]
    root, idx = deserialize_tree(tree_data)

    # lire données compressées
    encoded = bits[32 + tree_size:]

    return decode_bits(encoded, root)

# ---------------------------------------------------------
# 9. CLI
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Huffman Classic")
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
