#!/usr/bin/env python3


import base64
import hashlib

from Crypto import Random
from Crypto.Cipher import AES


def derivationKey(key: str, salt=b'@.11#%[]|Q1Wd;M\\,v\r@K22Heq&uw~[P'):
    return hashlib.pbkdf2_hmac('sha256', key.encode(), salt, 512 * 512)


def encrypt(key: str, cont: str):
    pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16) 

    dk = derivationKey(key)
    cont = pad(cont).encode()
    iv = Random.new().read(16)

    cipher = AES.new(dk, AES.MODE_CBC, iv)

    return base64.b64encode(iv + cipher.encrypt(cont)).decode()


def decrypt(key: str, cont: str):
    unpad = lambda s : s[:-ord(s[len(s)-1:])]

    dk = derivationKey(key)
    cont = base64.b64decode(cont.encode())
    iv = cont[:16]

    cipher = AES.new(dk, AES.MODE_CBC, iv)

    return unpad(cipher.decrypt(cont[16:])).decode()
