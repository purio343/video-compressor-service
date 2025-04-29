import socket
import json
import sys
import os

with open("config.json", "r") as f:
    config = json.load(f)

server_address = config["server_address"]
server_port = config["server_port"]

def main():
    file_path = input("Type the path of the file you want to upload: ")
    if not os.path.exists(file_path):
        print(f'File not found: {file_path}')
        sys.exit(1)
    tcp_handler(file_path)

def tcp_handler(file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_address, server_port))
        send_file(sock, file_path)
        receive_response(sock)
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)
    finally:
        sock.close()
    
def send_file(sock, file_path):
    try:
        with open(file_path, "rb") as f:
            filesize = os.path.getsize(file_path)
            header = filesize.to_bytes(32, 'big')
            sock.sendall(header)

            data = f.read(1400)
            while data:
                print(f'Sending {len(data)} bytes')
                sock.sendall(data)
                data = f.read(1400)
    except FileNotFoundError as e:
        print(f'File not found: {e}')
        sys.exit(1)

def receive_response(sock):
    try:
        response = sock.recv(16)
        print(f'{response.decode()}')
    except socket.error as e:
        print(f'Error receiving response: {e}')
        sys.exit(1)

if __name__ == "__main__":
    main()