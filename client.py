import socket
import json
import sys
import os
import math
import time
from tqdm import tqdm
from utils import *

def main():
    config = load_config()
    server_info = (config["server_address"], config["server_port"])

    while True:
        file_path = input("Type the path of the file you want to upload: ")
        json_path = input("Type the path of the json file: ")
        if not os.path.exists(file_path):
            print(f'File not found: {file_path}')
        elif not os.path.exists(json_path):
            print(f'Json file not found: {json_path}')
        else:
            break

    tcp_handler(file_path, json_path, server_info)

def tcp_handler(file_path, json_path, server_info):
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.settimeout(15)
        tcp_sock.connect(server_info)
        send_file(tcp_sock, file_path, json_path)
        json_file, media_type, payload = receive_response(tcp_sock)
        print(f'Recieved response')
        print('json_file: ')
        print(json_file)
        print(f'media_type: {media_type}')
        filepath = save_data('compressed', payload, media_type)
        print(f'saved movie: {filepath}')
    except socket.timeout:
        print('This connection is time out.')
        sys.exit(1)
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)
    finally:
        tcp_sock.close()
    
def send_file(sock, file_path, json_path):
    try:
        filesize = os.path.getsize(file_path)
        if check_filesize(filesize):
            print("File size is too large")
            sys.exit(1)
        # jsonファイルの長さ
        json_length = os.path.getsize(json_path)
        media_type = os.path.splitext(file_path)[1].encode()
        media_type_length = len(media_type)
        header = handle_mmp_header(json_length, media_type_length, filesize)
        sock.sendall(header)

        json_file = b''
        with open(json_path, 'rb') as f:
            json_file = f.read()

        # body = json_file + media_type + payload
        # sock.sendall(body)
        sock.sendall(json_file)
        sock.sendall(media_type)

        # 動画ファイルを送信
        with open(file_path, 'rb') as f:
            data = f.read(4000)
            while data:
                print('Sending data...')
                sock.sendall(data)
                data = f.read(4000)

    except FileNotFoundError as e:
        print(f'File not found: {e}')
        sys.exit(1)

def handle_mmp_header(json_length, media_type_length, filesize_length):
    header = json_length.to_bytes(2, 'big')
    header += media_type_length.to_bytes(1, 'big')
    header += filesize_length.to_bytes(5, 'big')
    return header

def receive_response(sock):
    try:
        header = sock.recv(8)
        json_length = int.from_bytes(header[:2], 'big')
        media_type_length = int.from_bytes(header[2:3], 'big')
        payload_length = int.from_bytes(header[3:8], 'big')
        
        json_file = sock.recv(json_length).decode()
        media_type = sock.recv(media_type_length).decode()
        payload = recv_movie(sock, payload_length)
        return [json_file, media_type, payload]
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