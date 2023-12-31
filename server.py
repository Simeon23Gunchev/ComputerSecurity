import base64
import socket
import threading
import json
import ssl
import time
import uuid
import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from KeyManager import KeyManager

class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.clients = {}
        self.session_tokens = {}
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip, port))
        self.server_socket.listen()
        self.key = KeyManager.get_key()

    def generate_session_token(self):
        return str(uuid.uuid4())

    def is_session_valid(self, token, user_id):
        return self.session_tokens.get(user_id) == token

    def listen(self):
        print(f"Server listening on {self.ip}:{self.port}")
        channel = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        channel.load_cert_chain(certfile='cert.pem', keyfile='key.pem')

        with channel.wrap_socket(self.server_socket, server_side=True) as server_ssl_socket:
            while True:
                client, address = server_ssl_socket.accept()
                threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client_socket):
        failed_attempts = 0
        max_attempts = 3
        client_request = []

        while True:
            try:
                current_time = time.time()
                client_request = [t for t in client_request if current_time - t < 60]

                if len(client_request) >= 10:
                    print("Limit exceeded")
                    continue

                client_request.append(current_time)
                encrypted_message = client_socket.recv(1024).decode()

                if not encrypted_message:
                    break

                message = self.decrypt_data(encrypted_message)

                if not message:
                    break

                if len(message) > 1024:
                    client_socket.send("ERROR: Data packet too large".encode())
                    continue

                response = self.process_request(message)

                if response.startswith("ERROR") and "Invalid credentials" in response:
                    failed_attempts += 1
                    if failed_attempts >= max_attempts:
                        client_socket.send("ERROR: Too many failed login attempts".encode())
                        break

                client_socket.send(response.encode())

            except json.JSONDecodeError:
                client_socket.send("ERROR: Invalid JSON format".encode())

            except socket.error as e:
                print(f"Socket error: {e}")
                break

            except Exception as e:
                print(f"Error: {e}")
                break

    def decrypt_data(self, encrypted_data):
        aesgcm = AESGCM(self.key)
        try:
            encrypted_data_bytes = base64.b64decode(encrypted_data)
            nonce, ciphertext = encrypted_data_bytes[:12], encrypted_data_bytes[12:]
            decrypted_str = aesgcm.decrypt(nonce, ciphertext, None).decode()
            decrypted_json = json.loads(decrypted_str)
            return decrypted_json
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

    def handle_registration(self, data):
        login_fields = ['id', 'password']
        if not all(field in data for field in login_fields):
            return "ERROR: Login error"

        user_id = data['id']
        password = data['password']

        with self.lock:
            if user_id not in self.clients:
                self.clients[user_id] = {'password': self.hash_password(password), 'counter': 0}
            else:
                if not self.check_password(self.clients[user_id]['password'], password):
                    return "ERROR: Invalid credentials"

            token = self.generate_session_token()
            self.session_tokens[user_id] = token
            response = {"status": "Successful login", "token": token}
            return json.dumps(response)

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def check_password(stored_password, provided_password):
        return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()

    def process_request(self, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return "ERROR: Invalid format"

        if 'action' not in data or 'amount' not in data:
            return self.handle_registration(data)
        else:
            required_fields = ['id', 'password', 'action', 'amount']
            if not all(field in data for field in required_fields):
                return "ERROR: Missing required data fields"

        token = data.get('token')
        client_id = data['id']

        if not self.is_session_valid(token, client_id):
            return "ERROR:Invalid session"

        password = data['password']
        action = data.get('action')

        try:
            amount = int(data.get('amount', 0))
            if amount < 0:
                return "ERROR: Unsupported data type or value for amount."
        except ValueError:
            return "ERROR: Unsupported data type or value for amount."

        with self.lock:
            if client_id not in self.clients or self.check_password(self.clients[client_id]['password'], password):
                if client_id not in self.clients:
                    self.clients[client_id] = {'password': password, 'counter': 0}

                if action == 'INCREASE':
                    self.clients[client_id]['counter'] += amount
                    self.log_counter_change(client_id)
                    return f"ACK: Counter updated to {self.clients[client_id]['counter']}"
                elif action == 'DECREASE':
                    self.clients[client_id]['counter'] -= amount
                    self.log_counter_change(client_id)
                    return f"ACK: Counter updated to {self.clients[client_id]['counter']}"
                # self.log_counter_change(client_id)
                else:
                    return "ERROR: Unsupported action."
            else:
                return "ERROR: Invalid credentials"

    def log_counter_change(self, client_id):
        with open("server_log.txt", "a") as file:
            file.write(f"{client_id}: {self.clients[client_id]['counter']}\n")


if __name__ == "__main__":
    try:
        server = Server("127.0.0.1", 65431)
        server.listen()
    except OSError as e:
        print(f"Error starting server: {e}")
    except KeyboardInterrupt:
        print("Server shutting down.")
