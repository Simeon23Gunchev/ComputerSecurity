from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import socket
import json
import time
import sys

#Alexandra Zamfir i6273294
#Mihaela Stanoeva i6273299
#Anna Nowowiejska i6289598
#Simeon Gunchev i6242650
#Adelin Birzan i6285129
class Client:
    def __init__(self, config_file):
        with open(config_file, 'r') as file:
            self.config = json.load(file)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.key = b'secret' 

    def connect(self):
        self.socket.connect((self.config['server']['ip'], self.config['server']['port']))
        registration_data = json.dumps({"id": self.config['id'], "password": self.config['password']})
        self.socket.send(registration_data.encode())
        response = self.socket.recv(1024).decode()
        print(f"Server response: {response}")

    def perform_actions(self):
        for action in self.config['actions']['steps']:
            if action.startswith("INCREASE") or action.startswith("DECREASE"):
                command, amount = action.split()
                amount = int(amount)
                action_data = json.dumps(
                    {"id": self.config['id'], "password": self.config['password'], "action": command, "amount": amount})
                self.socket.send(action_data.encode())
                response = self.socket.recv(1024).decode()
                print(f"Server response: {response}")
                time.sleep(self.config['actions']['delay'])

    def start(self):
        self.connect()
        self.perform_actions()
        self.socket.close()

    def encrypt_data(self, data):
        data_bytes = json.dumps(data).encode('utf-8')
        nonce = AESGCM.generate_nonce()
        cipher = AESGCM(self.key)
        ciphertext = cipher.encrypt(nonce, data_bytes, None)
        return base64.b64encode(nonce + ciphertext)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py <config_file>")
        sys.exit(1)

    client = Client(sys.argv[1])
    client.start()
