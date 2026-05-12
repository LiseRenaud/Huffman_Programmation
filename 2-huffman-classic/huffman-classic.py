import heapq
from collections import Counter
import argparse
import time

# la classe Node représente les nœuds de l'arbre de Huffman, avec les attributs byte (le caractère associé au nœud),
# freq (la fréquence du caractère), left (le nœud fils gauche) et right (le nœud fils droit). 
# La méthode is_leaf permet de vérifier si un nœud est une feuille càd s'il a un caractère associé.
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


# construit l'arbre de huffman a partir des fréquences de caractères, en utilisant une file de priorité pour maintenir les noeuds triés par fréquence.
def build_tree(freq):
    heap = []
    order = 0
    # création de noeuds pour chaque cractère et insertion dans la file de priorité
    for b, f in freq.items():
        heap.append(Node(b, f, order=order))
        order += 1
    heapq.heapify(heap)

    #si il n'y a qu'un seul caractère alors on crée un noeud interne avec ce caractère comme feuille gaucheet une feuille vide à sa droite, pour éviter de laisser une arbre avec une seul feuille
    if len(heap) == 1:
        n = heap[0]
        return Node(None, n.freq, n, None, order=order)
    next_order = order
    # tant qu'il y a un noeud dans la file de priorité, on extrait les noeuds de plus petite fréquence
    # on crée un noeud parent avec une fréquence égale à la somme des fréquences des enfants et on le réinsère dans la file de priorité jusqu'à ce qu'il ne reste plus qu'un seul noeud qui sera la racine de l'arbre de Huffman.
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


# construction de la table de code à partir de l'arbre de huffman,
# on parcourt l'arbre de manière récursive et on ajoute 0 en allant dans le branche de gauche et 1 à celles de droite, 
# jusqu'à atteindre la fin d'une branche --> une feuille/un caractère auquel on associe le code binaire construit qu'on ajoute à notre table.
def build_codes(node, prefix="", codes=None):
    if codes is None:
        codes = {}

    if node.is_leaf():
        codes[node.byte] = prefix or "0"
        return codes

    build_codes(node.left, prefix + "0", codes)
    build_codes(node.right, prefix + "1", codes)
    return codes


# convertit une chaîne de bits en bytes, en ajoutant des bits de padding à la fin si nécessaire pour que la longueur soit un multiple de 8, 
# retourne le nombre de bits de padding ajoutés ainsi que les bytes résultants.
def pack(bits):
    pad = (8 - len(bits) % 8) % 8
    bits += "0" * pad

    out = bytearray()
    for i in range(0, len(bits), 8):
        out.append(int(bits[i:i+8], 2))

    return pad, bytes(out)

# inverse de pack, on convertit les bytes en bits et on enlève les bits de padding à la fin si nécessaire.
def unpack(pad, data):
    bits = "".join(f"{b:08b}" for b in data)
    return bits[:-pad] if pad else bits


# formatte et affiche l'arbre de huffman
# indique si un nœud est une feuille en affichant le caractère associé et sa fréquence, 
# ou s'il s'agit d'un nœud interne en affichant un astérisque et la somme des fréquences de ses enfants.
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


# on encode le texte caractère par caractère en utilisant les codes associés via la table des codes.
# si un caractère n'est pas dans la table 
# alors on encode d'abord un caractère d'échappement puis on encode le caractère en binaire sur 8 bits et on ajoute à la chaîne de bits résultante.
def encode(inp, outp):
    start = time.time()

    # lit le fichier d'entrée en binaire et calcule la taille originale du fichier
    data = open(inp, "rb").read()
    original_size = len(data)

    freq = Counter(data)
    # construit l'arbre de huffman à partir des fréquences de caractères, 
    # puis la table de codes à partir de l'arbre 
    # puis encode le texte en une chaîne de bits en utilisant les codes associés à chaque caractère.
    tree = build_tree(freq)
    codes = build_codes(tree)

    bitstring = "".join(codes[b] for b in data)

    pad, encoded = pack(bitstring)

    # crée le fichier de sortie en binaire
    with open(outp, "wb") as f:
        f.write(bytes([pad]))
        f.write(len(freq).to_bytes(4, "big"))

        # écrit les fréquences de chaque caractère dans le fichier de sortie, 
        # utilise 1 byte pour le caractère et 4 bytes pour la fréquence, suivi de la chaîne de bits encodée.
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



def decode(inp, outp):
    start = time.time()
    #lit le fichier d'entrée en binaire
    with open(inp, "rb") as f:
        pad = f.read(1)[0]
        n = int.from_bytes(f.read(4), "big")

    # récupère les fréquences de chaque caractère à partir du fichier d'entrée,
    # utilise 1 byte pour le caractère et 4 bytes pour la fréquence, suivi de
    # la chaîne de bits encodée.
        freq = {}
        for _ in range(n):
            b = f.read(1)[0]
            fr = int.from_bytes(f.read(4), "big")
            freq[b] = fr

        data = f.read()
    # reconstruit l'arbre de huffman à partir des fréquences de caractères
    tree = build_tree(freq)

    print("\n===== ARBRE RECONSTRUIT =====")
    print_tree(tree)
    
    # convertit les bytes en bits et enlève les bits de padding à la fin si nécessaire,
    bits = unpack(pad, data)

    result = bytearray()
    node = tree
     # on decode les bits en parcourant l'arbre de huffman à partir de la racine, 
     # en suivant les branches de gauche pour les bits 0 et les branches de droite pour les bits 1, 
     # jusqu'à atteindre une feuille qui correspond à un caractère, auquel on ajoute le caractère décodé à la chaîne de résultat et on recommence à partir de la racine pour les bits suivants.
    for bit in bits:
        node = node.left if bit == "0" else node.right
        if node.is_leaf():
            result.append(node.byte)
            node = tree

    open(outp, "wb").write(result)

    end = time.time()

    print(f"\nTemps de décompression : {end - start:.4f} secondes")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", action="store_true")
    parser.add_argument("-d", action="store_true")
    parser.add_argument("-o", required=True)
    parser.add_argument("input")

    args = parser.parse_args()
    # appelle encode et decode en fonction des arguments passés en ligne de commande,
    if args.e:
        encode(args.input, args.o)
    elif args.d:
        decode(args.input, args.o)


if __name__ == "__main__":
    main()