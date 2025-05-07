import ffmpeg
import os
import json

def compress_video(file_path):
    print(f'filepath: {file_path}')
    output_path = os.path.splitext(file_path)[0] + '_compressed.mp4'
    # 加工処理
    try:
        ffmpeg.input(file_path).output(output_path, crf=28).run()
    except ffmpeg.Error as e:
        print(f'Failed to compress: {e.stderr.decode()}') 
    
    video_info = json.dumps(ffmpeg.probe(output_path), indent=2)
    
    return [output_path, video_info]

# Todo: 出力後のファイルに何故か音がない
def convert_definition(file_path, definition):
    width = int(definition["width"])
    height = int(definition["height"])
    output_path = os.path.splitext(file_path)[0] + '_convert_definition.mp4'
    # 加工処理
    try:
        ffmpeg.input(file_path).filter('scale', width, height).output(output_path).run()
    except ffmpeg.Error as e:
        print(f'Failed to convert definition: {e.stderr.decode()}')
        
    video_info = json.dumps(ffmpeg.probe(output_path), indent=2)

    return [output_path, video_info]

# Todo: 指定されたアスペクト比に変換された動画を返す。加工処理でエラーになる。
def change_aspect_ratio(file_path, aspect_ratio):
    width, height = map(int, aspect_ratio.split(':'))
    output_path = os.path.splitext(file_path)[0] + '_changed_aspect.mp4'
    aspect_filter = f"setsar=1,pad=iw*{height}/{width}:ih:(ow-iw)/2:(oh-ih)/2"
    # 加工処理
    try:
        ffmpeg.input(file_path).output(output_path, vf=aspect_filter).run()
    except ffmpeg.Error as e:
        print(f'Failed to change aspect ratio: {str(e)}')
    
    video_info = json.dumps(ffmpeg.probe(output_path), indent=2)

    return [output_path, video_info]

# Todo: 音声だけを抽出したMP3を返す。
def extract_audio(file_path):
    return ""

# Todo: 指定された時間範囲を切り取ってGIFまたはWEBMを返す。
def convert_gif(file_path):
    return ""
