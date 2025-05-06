import ffmpeg
import os
import json

def compress_video(file_path):
    print(f'filepath: {file_path}')
    output_path = os.path.splitext(file_path)[0] + '_compressed.mp4'
    ffmpeg.input(file_path).output(output_path, crf=28).run()
    video_info = json.dumps(ffmpeg.probe(output_path), indent=2)
    
    return [output_path, video_info]
