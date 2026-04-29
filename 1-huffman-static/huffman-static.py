#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
from PriorityQueue import PriorityQueue

freq = {"a":7, "b":1, "c":3, "d":4, "e":12, "f":1, "g":1, "h":1, "i":6, "j":0, 
        "k":0, "l":5, "m":3, "n":6, "o":5, "p":2, "q":0, "r":6, "s":6, "t":6, 
        "u":4, "v":1, "w":0, "x":0, "y":0, "z":0, "à":0, "é":2, "è":0, ",":2, 
        "-":0, ".":1, ";":0, "!":0, "?":0, "\n":0, "<sp>":15}

def encrypt(text):
    pass

def decrypt(text):
    pass

def main():
    parser = argparse.ArgumentParser(description="Encrypt Decrypt and output files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encrypt", action="store_true", help="Encrypt the input text")
    group.add_argument("-d", "--decrypt", action="store_true", help="Decrypt the input text")
    
    parser.add_argument("input_path", type=str, help="Path to the input file")
    parser.add_argument("-o", "--output", type=str, required=True,help="Output the encrypted text or decrypted to a file")
    
    args = parser.parse_args()

    if args.encrypt:
        with open(args.input_path, 'r') as file:
            text = file.read()
        encrypted_text = encrypt(text)
        with open(args.output, 'w') as file:
            file.write(encrypted_text)
    
    elif args.decrypt:
        with open(args.input_path, 'r') as file:
            text = file.read()
        decrypted_text = decrypt(text)
        with open(args.output, 'w') as file:
            file.write(decrypted_text)
    pass

if __name__ == "__main__":
    main()