import socket
import threading
import sys
import json
import time
import os

def main():
     config = load_config()
     current_size = calc_movie_size()
     if current_size > config["max_total_capacity"]:
          print('You can not upload any more videos.')
          sys.exit(1)
     print(f'Saved movies size: {current_size}')
     server_info = (config["server_address"], config["server_port"])
     tcp_handler(server_info)

def tcp_handler(server_info):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_info)
    sock.listen(10)

    print(f'Server is running on {server_info}')

    while True:
        connection, address = sock.accept()
        handle_client_thread = threading.Thread(target=handle_client, args=(connection, address), daemon=True)
        handle_client_thread.start()
        
def handle_client(connection, address):
     try:
          header = connection.recv(32)
          print('Received header')
          filesize = int.from_bytes(header, "big")
          print(f'Filesize: {filesize}')
          data = receive_movie_data(connection, filesize)
          print('Received movie data')
          if not is_mp4(data):
               raise Exception("File is not mp4")
          
          # レスポンスは16バイト
          response = create_response()
          connection.sendall(response)
          print('Sent response')

          save_data(data)

     except Exception as e:
          print(f'{str(e)}')
          # 16バイト
          error_res = b'400 ERR \x00\x00\x00\x00\x00\x00\x00\x00'
          connection.sendall(error_res)
     finally:
          connection.close()

# 受信したバイト列からmp4かどうかを判断
def is_mp4(data: bytes):
     return b'ftyp' in data[:12]

def create_response():
     # 3桁＋空白で4バイト
    status_code = b'200 '
    # ファイル種別, 4バイト
    file_type = b'MP4 '
    # 予備領域, 4バイト
    reserved1 = b'\x00\x00\x00\x00'
    # 予備領域, 4バイト
    reserved2 = b'\x00\x00\x00\x00'

    return status_code + file_type + reserved1 + reserved2

def receive_movie_data(connection, filesize):
     data = b''
     while len(data) < filesize:
          chunk = connection.recv(min(filesize - len(data), 1400))
          if not chunk:
               raise Exception("Connection is closed")
          data += chunk
          
     return data

def load_config(path='config.json'):
     try:
          with open(path, 'r') as f:
               return json.load(f)
     except FileNotFoundError:
          print(f'Config file not found: {path}')
          sys.exit(1)
     except json.JSONDecodeError:
          print(f'Invalid JSON format in config file: {path}')
          sys.exit(1)

def save_data(data: bytes):
     folder = 'uploaded'
     filename = f'{str(time.time())}.mp4'
     filepath = os.path.join(folder, filename)

     if not os.path.exists(folder):
          os.makedirs(folder)

     with open(filepath, 'wb') as f:
          f.write(data)

def calc_movie_size(path='uploaded'):
     total = 0
     if not os.path.exists(path):
          print('Uploaded file is none')
          return total
     
     for movie in os.listdir(path):
          movie_path = os.path.join(path, movie)
          if os.path.isfile(movie_path):
               total += os.path.getsize(movie_path)

     return total

if __name__ == "__main__":
    main()