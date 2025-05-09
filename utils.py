import os
import time
import socket

def recv_movie(connection: socket.socket, filesize: int) -> bytes:
    data = b''
    while len(data) < filesize:
        chunk = connection.recv(min(1400, filesize - len(data)))
        if not chunk:
            raise Exception('Connection is closed')
        data += chunk
    
    return data

def send_movie(connection: socket.socket, filepath: str) -> None:
    with open(filepath, 'rb') as f:
        data = f.read(4000)
        while data:
            connection.sendall(data)
            print('Sending data...')
            data = f.read(4000)

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

# 動画保存用の処理
def save_data(folder: str, data: bytes, media_type: str) -> str:
    if folder.strip() == 'compressed':
        filename = f'compressed_{str(time.time())}.{media_type}'
    else:
        filename = f'{str(time.time())}.{media_type}'

    if not os.path.exists(folder):
        os.makedirs(folder)

    # 動画保存時のパス
    file_path = os.path.join(folder, filename)

    with open(file_path, 'wb') as f:
        f.write(data)
    
    return file_path

def handle_mmp_header(json_length, media_type_length, filesize_length):
    # jsonサイズ：2バイト
    header = json_length.to_bytes(2, 'big')
    # メディアタイプのサイズ：1バイト
    header += media_type_length.to_bytes(1, 'big')
    # 動画ファイルサイズ：5バイト
    header += filesize_length.to_bytes(5, 'big')
    return header