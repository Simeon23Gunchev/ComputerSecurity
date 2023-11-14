import socket
import time
import json


def start_client(config_file, max_retries=5):
    retries = 0

    while retries < max_retries:
        try:
            with open(config_file, "r") as file:
                config = json.load(file)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((config["server"]["ip"], config["server"]["port"]))

                s.send(json.dumps({"id": config["id"], "password": config["password"]}).encode())
                response = s.recv(1024).decode()

                if response == "ACK":
                    print("Login successful")

                    for action in config["actions"]["steps"]:
                        print(f"Performing action: {action}")
                        s.send(action.encode())
                        time.sleep(config["actions"]["delay"])

                    print("Logging out...")
                    s.send("LOGOUT".encode())

                    break  # Exit loop after successful connection and operations

                else:
                    print("Registration failed")
                    break

        except Exception as e:
            print(f"Connection failed: {e}")
            retries += 1
            time.sleep(2)  # Wait before retrying

        if retries >= max_retries:
            print("Max reconnection attempts reached. Exiting.")

start_client("client_config.json")