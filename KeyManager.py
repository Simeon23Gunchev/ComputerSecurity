import os

class KeyManager:
    _key_file = 'keyfile.bin'

    @classmethod
    def generate_key(cls):
        if not os.path.exists(cls._key_file):
            key = os.urandom(32)
            with open(cls._key_file, 'wb') as file:
                file.write(key)
        return cls.get_key()

    @classmethod
    def get_key(cls):
        if not os.path.exists(cls._key_file):
            return cls.generate_key()
        with open(cls._key_file, 'rb') as file:
            return file.read()
