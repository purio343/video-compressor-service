import socket
import json
import sys
import os
import math

def main():
    config = load_config()
    server_info = (config["server_address"], config["server_port"])

    file_path = input("Type the path of the file you want to upload: ")
    if not os.path.exists(file_path):
        print(f'File not found: {file_path}')
        sys.exit(1)
    tcp_handler(file_path, server_info)

def tcp_handler(file_path, server_info):
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect(server_info)
        send_file(tcp_sock, file_path)
        receive_response(tcp_sock)
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)
    finally:
        tcp_sock.close()
    
def send_file(sock, file_path):
    try:
        with open(file_path, "rb") as f:
            filesize = os.path.getsize(file_path)
            if check_filesize(filesize):
                print("File size is too large")
                sys.exit(1)
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

def load_config(path="config.json"):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f'Config file not found: {path}')
        sys.exit(1)
    except json.JSONDecodeError:
        print(f'Invalid JSON format in config file: {path}')
        sys.exit(1)

def check_filesize(filesize):
    return filesize > math.pow(2, 32)

if __name__ == "__main__":
    main()