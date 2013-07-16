import os
from nacl import public


class Error(Exception):
    pass


class TestBox(object):
    """Fake crypto for testing."""

    def encrypt(self, data):
        pk = public.PublicKey(public_key)
        return '{crypt}' + data

    def decrypt(self, data):
        if not data.startswith('{crypt}'):
            raise Error('decryption error')
        return data[7:]


class Box(object):
    """Crypto box for safe communication between two keypairs."""

    def __init__(self, username, src_key, dst_key):
        self._prefix = username
        self._src = src_key
        self._dst = dst_key
        self._box = public.Box(
            public.PrivateKey(src_key),
            public.PublicKey(dst_key))

    def encrypt(self, data):
        r = os.urandom(max(12, self._box.NONCE_SIZE - len(self._prefix)))
        nonce = (self._prefix + r)[-self._box.NONCE_SIZE:]
        return self._box.encrypt(data, nonce)

    def decrypt(self, ciphertext):
        return self._box.decrypt(ciphertext)


def generate_keys():
    key = public.PrivateKey.generate()
    return bytes(key), bytes(key.public_key)


if __name__ == '__main__':
    # Generate a secret/public keypair.
    import sys
    if len(sys.argv) != 3:
        print >>sys.stderr, "Usage: crypto.py <secret-key-file> <public-key-file>"
        sys.exit(1)
    secret_key_path, public_key_path = sys.argv[1:]
    secret, public = generate_keys()
    with open(secret_key_path, 'w') as fd:
        fd.write(secret)
    with open(public_key_path, 'w') as fd:
        fd.write(public)

