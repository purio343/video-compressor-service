import socket
import threading
import json
import math

with open("config.json", "r") as f:
        config = json.load(f)

def main():
    tcp_thread = threading.Thread(target=tcp_handler, daemon=True)
    tcp_thread.start()
    tcp_thread.join()

def tcp_handler():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((config["server_address"], config["server_port"]))
    sock.listen(10)

    print(f'Server is running on {config["server_address"]}:{config["server_port"]}')

    while True:
        connection, address = sock.accept()
        try:
             header = connection.recv(32)
             print('Received header')
             filesize = int.from_bytes(header, "big")
             print(f'Filesize: {filesize}')
             # ファイルが4GBを超える場合はエラー
             if not check_filesize(filesize):
                  raise Exception("File size is too large")
             print('Checked filesize')
             data = receive_movie_data(connection, filesize)
             print('Received movie data')
             if not is_mp4(data):
                  raise Exception("File is not mp4")
             
             # レスポンスは16バイト
             response = create_response()
             connection.sendall(response)
             print('Sent response')

        except Exception as e:
             print(f'{str(e)}')
        finally:
             connection.close()

def check_filesize(filesize):
    return filesize <= math.pow(2, 32)

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

if __name__ == "__main__":
    main()