import socket
import threading
import sys
import json
import time
import os
from backend.editing import *
from utils import *

def main():
     config = load_config()
     # 加工処理した動画は削除するため一旦無効化
     # current_size = calc_movie_size()
     # if current_size > config["max_total_capacity"]:
     #      print('You can not upload any more videos.')
     #      sys.exit(1)
     # print(f'Saved movies size: {current_size}')
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
          # ヘッダーは8バイト
          header = connection.recv(8)
          print('Received header')

          json_length = int.from_bytes(header[:2], 'big')
          media_type_length = int.from_bytes(header[2:3], 'big')
          payload_length = int.from_bytes(header[3:8], 'big')
          
          json_file = connection.recv(json_length)
          media_type = connection.recv(media_type_length).decode('utf-8')
          # 動画ファイル
          payload = recv_movie(connection, payload_length)
          # 処理前の動画を保存してパスを返す
          file_path = save_data('uploaded', payload)
          print(f'before compressed data_size: {os.path.getsize(file_path)}')
          # 送信されたjsonファイルから要求されたリクエストを読み取る
          json_dic = json.loads(json_file.decode())
          operation = json_dic['operation']

          # クライアントからの情報の確認 -> ok
          print(f'mediatype: {media_type}')
          print(f'operation: {operation}')
          print(f'saved_filepath: {file_path}')

          # リクエストと動画データを基に処理を行って、その動画のバイト列と動画サイズ、パスと動画情報を返す
          data, data_size, compressed_path, video_info = handle_payload(operation, file_path, json_dic)         
          compressed_header, compressed_body = create_response(data, data_size, video_info)
          connection.sendall(compressed_header)
          connection.sendall(compressed_body)
          print('Sent response')
          # デバッグ用に保存した動画情報削除処理をコメントアウト
          # cleanup_movie_data(file_path, compressed_path)

     except Exception as e:
          print(f'{str(e)}')
          # 16バイト
          error_res = b'400 ERR \x00\x00\x00\x00\x00\x00\x00\x00'
          connection.sendall(error_res)
     finally:
          connection.close()

def handle_payload(operation, file_path, json_dic):
     if operation == 1:
          compressed_path, video_info = compress_video(file_path)
          compressed_size = os.path.getsize(compressed_path)
          data = b''
          with open(compressed_path, 'rb') as f:
               data = f.read()

          print(f'compressed video: {compressed_path}')
          return [data, compressed_size, compressed_path, video_info]
     elif operation == 2:
          definition = json_dic["definition"]
          compressed_path, video_info = convert_definition(file_path, definition)
          compressed_size = os.path.getsize(compressed_path)
          data = b''
          with open(compressed_path, 'rb') as f:
               data = f.read()
          
          print(f'converted definition movie: {compressed_path}')
          return [data, compressed_size, compressed_path, video_info]
     elif operation == 3:
          ratio = json_dic["ratio"]
          compressed_path, video_info = change_aspect_ratio(file_path, ratio)
          compressed_size = os.path.getsize(compressed_path)
          data = b''
          with open(compressed_path, 'rb') as f:
               data = f.read()
          
          print(f'changed ratio: {compressed_path}')
          return [data, compressed_size, compressed_path, video_info]
     
# 受信したバイト列からmp4かどうかを判断
def is_mp4(data: bytes):
     return b'ftyp' in data[:12]

def cleanup_movie_data(path, compressed_path):
     if os.path.exists(path):
          os.remove(path)
          print('delete movie data')
     else:
          print('movie data is none')
     if os.path.exists(compressed_path):
          os.remove(compressed_path)
          print('delete compressed movie data')
     else:
          print('compressed movie data is none')

def create_response(data, data_size, video_info):
     video_info_bytes = video_info.encode()
     # 2バイト
     json_length = len(video_info_bytes).to_bytes(2, 'big')
     # 1バイト, Todo:動的に返すようにする
     media_type_length = len(b'mp4 ').to_bytes(1, 'big')
     # 5バイト
     payload_length = data_size.to_bytes(5, 'big')

     header = json_length + media_type_length + payload_length
     # Todo: クライアントへの返信時のボディのJSONを含める。
     body = video_info_bytes + 'mp4 '.encode('utf-8') + data
     
     return [header, body]

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

if __name__ == "__main__":
    main()