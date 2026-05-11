import heapq
from collections import Counter
import argparse
import time


# =========================
# NODE
# =========================
class Node:
    def __init__(self, byte=None, freq=0, left=None, right=None, order=0):
        self.byte = byte
        self.freq = freq
        self.left = left
        self.right = right
        self.order = order  # pour affichage type TP

    def is_leaf(self):
        return self.byte is not None

    def __lt__(self, other):
        return self.freq < other.freq


# =========================
# BUILD TREE
# =========================
def build_tree(freq):
    heap = []
    order = 0

    for b, f in freq.items():
        heap.append(Node(b, f, order=order))
        order += 1

    heapq.heapify(heap)

    if len(heap) == 1:
        n = heap[0]
        return Node(None, n.freq, n, None, order=order)

    next_order = order

    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)

        parent = Node(
            None,
            a.freq + b.freq,
            a,
            b,
            order=next_order
        )
        next_order += 1

        heapq.heappush(heap, parent)

    return heap[0]


# =========================
# CODES
# =========================
def build_codes(node, prefix="", codes=None):
    if codes is None:
        codes = {}

    if node.is_leaf():
        codes[node.byte] = prefix or "0"
        return codes

    build_codes(node.left, prefix + "0", codes)
    build_codes(node.right, prefix + "1", codes)
    return codes


# =========================
# BIT PACK
# =========================
def pack(bits):
    pad = (8 - len(bits) % 8) % 8
    bits += "0" * pad

    out = bytearray()
    for i in range(0, len(bits), 8):
        out.append(int(bits[i:i+8], 2))

    return pad, bytes(out)


def unpack(pad, data):
    bits = "".join(f"{b:08b}" for b in data)
    return bits[:-pad] if pad else bits


# =========================
# TREE PRINT (FORMAT DEMANDÉ)
# =========================
def print_tree(node, indent="", is_left=True):
    if node is None:
        return

    prefix = "├── " if indent else ""

    if node.is_leaf():
        char = chr(node.byte)
        if node.byte == 10:
            char = "\\n"
        elif node.byte == 32:
            char = "space"

        print(f"{indent}{prefix}'{char}' ({node.byte}) [w={node.freq}, ord={node.order}]")
    else:
        print(f"{indent}{prefix}NYT/INT (w={node.freq}, ord={node.order})")

    new_indent = indent + ("│   " if indent else "    ")

    if node.left:
        print_tree(node.left, new_indent, True)
    if node.right:
        print_tree(node.right, new_indent, False)


# =========================
# ENCODE
# =========================
def encode(inp, outp):
    start = time.time()

    data = open(inp, "rb").read()
    original_size = len(data)

    freq = Counter(data)

    tree = build_tree(freq)
    codes = build_codes(tree)

    bitstring = "".join(codes[b] for b in data)

    pad, encoded = pack(bitstring)

    with open(outp, "wb") as f:
        f.write(bytes([pad]))
        f.write(len(freq).to_bytes(4, "big"))

        for b, fr in freq.items():
            f.write(bytes([b]))
            f.write(fr.to_bytes(4, "big"))

        f.write(encoded)

    end = time.time()

    compressed_size = len(encoded)
    ratio = (1 - compressed_size / original_size) * 100 if original_size else 0

    print("\n--- Compression terminée ---")
    print(f"Temps d'exécution : {end - start:.4f} secondes")

    print("\n===== ARBRE FINAL APRES COMPRESSION =====")
    print_tree(tree)

    print(f"\nTaille originale : {original_size} bytes")
    print(f"Taille compressée : {compressed_size} bytes")
    print(f"Compression : {ratio:.2f}%")


# =========================
# DECODE
# =========================
def decode(inp, outp):
    start = time.time()

    with open(inp, "rb") as f:
        pad = f.read(1)[0]
        n = int.from_bytes(f.read(4), "big")

        freq = {}
        for _ in range(n):
            b = f.read(1)[0]
            fr = int.from_bytes(f.read(4), "big")
            freq[b] = fr

        data = f.read()

    tree = build_tree(freq)

    print("\n===== ARBRE RECONSTRUIT =====")
    print_tree(tree)

    bits = unpack(pad, data)

    result = bytearray()
    node = tree

    for bit in bits:
        node = node.left if bit == "0" else node.right
        if node.is_leaf():
            result.append(node.byte)
            node = tree

    open(outp, "wb").write(result)

    end = time.time()

    print(f"\nTemps de décompression : {end - start:.4f} secondes")


# =========================
# MAIN
# =========================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", action="store_true")
    parser.add_argument("-d", action="store_true")
    parser.add_argument("-o", required=True)
    parser.add_argument("input")

    args = parser.parse_args()

    if args.e:
        encode(args.input, args.o)
    elif args.d:
        decode(args.input, args.o)


if __name__ == "__main__":
    main()