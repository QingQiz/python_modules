#!/usr/bin/env python3


def derivationKey(key: str, salt=b'@.11#%[]|Q1Wd;M\\,v\r@K22Heq&uw~[P'):
    import hashlib
    return hashlib.pbkdf2_hmac('sha256', key.encode(), salt, 512 * 512)


def encrypt(key: str, cont: str):
    import base64
    from Crypto import Random
    from Crypto.Cipher import AES

    pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16) 

    dk = derivationKey(key)
    cont = pad(cont).encode()
    iv = Random.new().read(16)

    cipher = AES.new(dk, AES.MODE_CBC, iv)

    return base64.b64encode(iv + cipher.encrypt(cont)).decode()


def decrypt(key: str, cont: str):
    import base64
    from Crypto import Random
    from Crypto.Cipher import AES

    unpad = lambda s : s[:-ord(s[len(s)-1:])]

    dk = derivationKey(key)
    cont = base64.b64decode(cont.encode())
    iv = cont[:16]

    cipher = AES.new(dk, AES.MODE_CBC, iv)

    return unpad(cipher.decrypt(cont[16:])).decode()


class JSON():
    @staticmethod
    def load(path, key):
        import os
        import json

        path = os.path.expanduser(path)
        path = os.path.expandvars(path)

        if os.path.exists(path):
            with open(path) as f:
                s = f.read()
                try:
                    return json.loads(s)
                except json.decoder.JSONDecodeError:
                    try:
                        return json.loads(decrypt(key, s))
                    except ValueError:
                        return None
        else:
            return None

    @staticmethod
    def dump(obj, path, key):
        import os
        import json

        path = os.path.expanduser(path)
        path = os.path.expandvars(path)

        # backup
        timeNow = __import__('datetime').datetime.now().timestamp()
        os.system(f'cp {path} /tmp/{os.path.basename(path)}.{timeNow}')

        with open(path, 'w+') as f:
            print(encrypt(key, json.dumps(obj)), file=f)


