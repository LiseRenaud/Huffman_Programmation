import heapq
from collections import Counter
import argparse


# =========================
# NODE
# =========================
class Node:
    def __init__(self, byte=None, freq=0, left=None, right=None):
        self.byte = byte
        self.freq = freq
        self.left = left
        self.right = right

    def is_leaf(self):
        return self.byte is not None

    def __lt__(self, other):
        return self.freq < other.freq


# =========================
# BUILD TREE
# =========================
def build_tree(freq):
    heap = [Node(b, f) for b, f in freq.items()]
    heapq.heapify(heap)

    if len(heap) == 1:
        n = heap[0]
        return Node(None, n.freq, n, None)

    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        heapq.heappush(heap, Node(None, a.freq + b.freq, a, b))

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
# PACK / UNPACK BITS
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
# ENCODE (UTF-8 SAFE)
# =========================
def encode(inp, outp):
    data = open(inp, "rb").read()   # 🔥 BYTES DIRECT

    freq = Counter(data)
    tree = build_tree(freq)
    codes = build_codes(tree)

    bitstring = "".join(codes[b] for b in data)

    pad, encoded = pack(bitstring)

    with open(outp, "wb") as f:
        f.write(bytes([pad]))
        f.write(len(freq).to_bytes(4, "big"))

        for b, fr in freq.items():
            f.write(bytes([b]))              # 1 byte EXACT
            f.write(fr.to_bytes(4, "big"))   # freq

        f.write(encoded)


# =========================
# DECODE
# =========================
def decode(inp, outp):
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

    bits = unpack(pad, data)

    result = bytearray()
    node = tree

    for bit in bits:
        node = node.left if bit == "0" else node.right

        if node.is_leaf():
            result.append(node.byte)
            node = tree

    open(outp, "wb").write(result)   # 🔥 write bytes


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