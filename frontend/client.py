import socket
import json
import sys
import os
import math
from tqdm import tqdm

def main():
    config = load_config()
    server_info = (config["server_address"], config["server_port"])

    while True:
        file_path = input("Type the path of the file you want to upload: ")
        if not os.path.exists(file_path):
            print(f'File not found: {file_path}')
        elif not file_path.lower().endswith('.mp4'):
            print('Only MP4 files are allowed.')
        else:
            break
    tcp_handler(file_path, server_info)

def tcp_handler(file_path, server_info):
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.settimeout(15)
        tcp_sock.connect(server_info)
        send_file(tcp_sock, file_path)
        status_code, file_type = receive_response(tcp_sock)
        print(f'Server > Status: {status_code}, Type: {file_type}')
    except socket.timeout:
        print('This connection is time out.')
        sys.exit(1)
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

            with tqdm(total=filesize, unit='B', unit_scale=True, desc='Uploading') as pbar:
                data = f.read(1400)
                while data:
                    sock.sendall(data)
                    pbar.update(len(data))
                    data = f.read(1400)
    except FileNotFoundError as e:
        print(f'File not found: {e}')
        sys.exit(1)

def receive_response(sock):
    try:
        response = sock.recv(16)
        status_code = response[:4].decode().strip()
        file_type = response[4:8].decode().strip()
        return [status_code, file_type]
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