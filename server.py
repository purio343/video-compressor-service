import socket
import threading
import sys
import json
import time
import os
from backend.editing import *
from utils import *

# 処理状況を保存
processing_status = {}
lock = threading.Lock()

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
        ip_address = str(address[0])
        # 一つのIPアドレスから複数の処理を受け付けない
        if ip_address in processing_status:
             print(f'The request from {ip_address} is processing...')
             connection.close()
             continue

        with lock:
             processing_status[ip_address] = {
                  "status": "processing",
                  "progress": 0
             }
        handle_client_thread = threading.Thread(target=handle_client, args=(connection, address), daemon=True)
        check_processing_thread = threading.Thread(target=check_processing_status, args=(str(address[0]),), daemon=True)
        handle_client_thread.start()
        check_processing_thread.start()
        
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
          save_folder = 'uploaded'
          # 処理前の動画を保存してパスを返す
          file_path = save_data(save_folder, payload, media_type)
          # 送信されたjson文字列から要求されたリクエストを読み取る
          json_dic = json.loads(json_file.decode())
          operation = json_dic['operation']
          # クライアントからの情報の確認
          print(f'mediatype: {media_type}')
          print(f'operation: {operation}')
          print(f'saved_filepath: {file_path}')

          # 加工前の動画パスを格納
          ip_address = str(address[0])
          with lock:
               processing_status[ip_address] = {
                    "file_path": file_path
               }

          # リクエストと動画データを基に処理を行って、その動画のバイト列と動画サイズ、パスと動画情報を返す 
          # また、処理状況を更新しながら動画の加工処理を行う        
          video_dic = handle_payload(operation, file_path, json_dic, ip_address)
          
          # 処理状況を管理する辞書を処理完了として更新
          with lock:
               processing_status[ip_address]["status"] = "completed"
               processing_status[ip_address]["progress"] = 100
               processing_status[ip_address]["file_path"] = video_dic["path"]
          
          # 加工データを基にレスポンス用のヘッダとボディを作成
          compressed_header, video_info, media_type = create_response(video_dic["bytes"], video_dic["size"], video_dic["info"])
          connection.sendall(compressed_header)
          connection.sendall(video_info)
          connection.sendall(media_type)
          send_movie(connection, video_dic["path"])
          print('Sent response')
          # 加工後のデータ送信後に、処理状況追跡用の辞書から対象のIPを削除
          with lock:
               del processing_status[ip_address]
          # 保存した動画情報を削除
          cleanup_movie_data(file_path, video_dic["path"])

     except Exception as e:
          print(f'{str(e)}')
          message = "時間をおいてもう一度送信してください。"
          err_dic = {
               "code": 400,
               "description": str(e),
               "solution": message
          }
          err_json = json.dumps(err_dic).encode('utf-8')
          header  = handle_mmp_header(len(err_json), 0, 0)
          connection.sendall(header)
          connection.sendall(err_json)
     finally:
          connection.close()

def handle_payload(operation, file_path, json_dic, ip_address):
     video_dic = {}

     def update_progress(progress: int):
          with lock:
               processing_status[ip_address]["progress"] = progress

     if operation == 1:
          update_progress(25)
          compressed_path, video_info = compress_video(file_path)
          update_progress(75)
          compressed_size = os.path.getsize(compressed_path)
          video_dic = {
               "bytes": get_movie_data(compressed_path),
               "size": compressed_size,
               "path": compressed_path,
               "info": video_info
          }
     elif operation == 2:
          definition = json_dic["definition"]
          update_progress(25)
          compressed_path, video_info = convert_definition(file_path, definition)
          update_progress(75)
          compressed_size = os.path.getsize(compressed_path)
          video_dic = {
               "bytes": get_movie_data(compressed_path),
               "size": compressed_size,
               "path": compressed_path,
               "info": video_info
          }
     elif operation == 3:
          ratio = json_dic["ratio"]
          update_progress(25)
          compressed_path, video_info = change_aspect_ratio(file_path, ratio)
          update_progress(75)
          compressed_size = os.path.getsize(compressed_path)
          video_dic = {
               "bytes": get_movie_data(compressed_path),
               "size": compressed_size,
               "path": compressed_path,
               "info": video_info
          }
     elif operation == 4:
          update_progress(25)
          compressed_path, audio_info = extract_audio(file_path)
          update_progress(75)
          compressed_size = os.path.getsize(compressed_path)
          video_dic = {
               "bytes": get_movie_data(compressed_path),
               "size": compressed_size,
               "path": compressed_path,
               "info": audio_info
          }
     elif operation == 5:
          split_time = json_dic["time"]
          update_progress(25)
          compressed_path, gif_info = convert_gif(file_path, split_time)
          update_progress(75)
          compressed_size = os.path.getsize(compressed_path)
          video_dic = {
               "bytes": get_movie_data(compressed_path),
               "size": compressed_size,
               "path": compressed_path,
               "info": gif_info
          }

     return video_dic
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
     print('加工後のデータ情報を表示')
     print(video_info)
     codec_name = video_info["streams"][0]["codec_name"]
     if codec_name == 'h264':
          media_type = "mp4"
     else:
          media_type = codec_name
     print("media_type")
     print(media_type)
     media_type_bytes = media_type.encode()
     video_info_bytes = json.dumps(video_info, indent=2).encode()
     header = handle_mmp_header(len(video_info_bytes), len(media_type_bytes), data_size)

     return [header, video_info_bytes, media_type_bytes]

def get_movie_data(path: str) -> bytes:
     with open(path, 'rb') as f:
          return f.read()

def check_processing_status(ip_address):
     while True:
          try:
               with lock:
                    if ip_address in processing_status and processing_status[ip_address]["status"] != "completed":
                         print(f'The request from {ip_address} is processing {processing_status[ip_address]["progress"]}%')
          except Exception as e:
               print(f'An error occurred in check_processing_status: {e}')
               break
          finally:
               time.sleep(60)

if __name__ == "__main__":
    main()