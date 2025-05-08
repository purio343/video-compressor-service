import os
import time

def recv_movie(connection, filesize) -> bytes:
    data = b''
    while len(data) < filesize:
        chunk = connection.recv(min(1400, filesize - len(data)))
        if not chunk:
            raise Exception('Connection is closed')
        data += chunk
    
    return data

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
    if folder == 'compressed':
        filename = f'compressed_{str(time.time())}.{media_type}'
    else:
        filename = f'{str(time.time())}.{media_type}'

    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, filename)

    with open(file_path, 'wb') as f:
        f.write(data)
    
    return file_path