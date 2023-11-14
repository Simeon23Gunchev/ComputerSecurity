import socket
import threading
import json

clients = {}
log_file = "server_log.txt"

def client_thread(conn, addr):
    client_id = None

    try:
        data = conn.recv(1024)
        if not data:
            print(f"No data received from {addr}. Closing connection.")
            return

        client_info = json.loads(data.decode())
        client_id = client_info['id']

        # Register or reconnect client
        if client_id in clients:
            if clients[client_id]['active']:
                conn.send("ERROR".encode())
                print(f"Duplicate connection attempt from {client_id}")
                return
            else:
                clients[client_id]['active'] = True
                conn.send("ACK".encode())
                print(f"Client {client_id} reconnected")
        else:
            clients[client_id] = {'counter': 0, 'active': True}
            conn.send("ACK".encode())
            print(f"New client {client_id} connected")

        # Handle client commands
        while True:
            data = conn.recv(1024).decode()
            if not data:
                print(f"Client {client_id} disconnected.")
                break

            if data.startswith("INCREASE") or data.startswith("DECREASE"):
                command, amount_str = data.split()
                amount = int(amount_str)

                if command == "INCREASE":
                    clients[client_id]['counter'] += amount
                elif command == "DECREASE":
                    clients[client_id]['counter'] -= amount

                log_entry = f"{client_id}: {clients[client_id]['counter']}\n"
                with open(log_file, "a") as log:
                    log.write(log_entry)
                print(f"Logged to file: {log_entry}")

            elif data == "LOGOUT":
                break

    except Exception as e:
        print(f"Error with client {client_id}: {e}")

    finally:
        if client_id and client_id in clients:
            clients[client_id]['active'] = False
            print(f"Connection with client {client_id} closed.")
        conn.close()

def start_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(5)
    print(f"Server listening on {ip}:{port}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=client_thread, args=(conn, addr)).start()

# Start the server
start_server("127.0.0.1", 65430)
