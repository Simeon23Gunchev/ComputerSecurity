import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import socket
import json
import time
import sys
import ssl

from KeyManager import KeyManager


class Client:
    def __init__(self, config_file):
        with open(config_file, 'r') as file:
            self.config = json.load(file)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.session_token = None
        self.key = KeyManager.get_key()

    def connect(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        self.socket = context.wrap_socket(self.socket, server_hostname=self.config['server']['ip'])
        self.socket.connect((self.config['server']['ip'], self.config['server']['port']))
        registration_data = json.dumps({"id": self.config['id'], "password": self.config['password']})
        encrypted_data = self.encrypt_data(registration_data)
        self.socket.send(encrypted_data.encode())
        response = self.socket.recv(1024).decode()
        self.session_token = self.extract_token(response)
        print(f"Server response: {response}")

    def extract_token(self, response):
        try:
            response_data = json.loads(response)
            return response_data.get('token')
        except json.JSONDecodeError:
            return None

    def perform_actions(self):
        for action in self.config['actions']['steps']:
            command, amount = action.split()
            try:
                amount = int(amount)
                action_data = json.dumps(
                    {"id": self.config['id'], "password": self.config['password'], "action": command, "amount": amount,
                     "token": self.session_token})
                encrypted_data = self.encrypt_data(action_data)
                self.socket.send(encrypted_data.encode())
                # self.socket.send(action_data.encode())
                response = self.socket.recv(1024).decode()
                if response.startswith("ERROR:"):
                    print(f"Server response: {response}")
                    self.socket.close()
                    sys.exit(1)
                print(f"Server response: {response}")
                time.sleep(self.config['actions']['delay'])


            except ValueError:
                print("Error: Unsupported data type or value for amount.")
                self.socket.close()
                sys.exit(1)

    def start(self):
        self.connect()
        self.perform_actions()
        print("Logged out")
        self.socket.close()

    def encrypt_data(self, data):
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        data_bytes = json.dumps(data).encode()
        ciphertext = aesgcm.encrypt(nonce, data_bytes, None)
        return base64.b64encode(nonce + ciphertext).decode()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py <config_file>")
        sys.exit(1)

    client = Client(sys.argv[1])
    client.start()
