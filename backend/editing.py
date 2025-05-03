import ffmpeg
import os

def compress_video(file_path):
    output_path = os.path.splittext(file_path)[0] + '_compressed.mp4'
    ffmpeg.input(file_path).output(output_path, crf=28).run()
    return output_path
