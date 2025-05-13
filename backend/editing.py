import ffmpeg
import os

def compress_video(file_path):
    print(f'filepath: {file_path}')
    output_path = os.path.splitext(file_path)[0] + '_compressed.mp4'
    # 加工処理
    try:
        ffmpeg.input(file_path).output(output_path, crf=28).run()
    except ffmpeg.Error as e:
        print(f'Failed to compress: {e.stderr.decode()}') 
    
    video_info = ffmpeg.probe(output_path)
    return [output_path, video_info]

def convert_definition(file_path, definition):
    width = int(definition["width"])
    height = int(definition["height"])
    resize_filter = f'scale={width}:{height}'
    output_path = os.path.splitext(file_path)[0] + '_convert_definition.mp4'
    # 加工処理
    try:
        ffmpeg.input(file_path).output(output_path, vf=resize_filter).run()
    except ffmpeg.Error as e:
        print(f'Failed to convert definition: {e.stderr.decode()}')
        
    video_info  = ffmpeg.probe(output_path)

    return [output_path, video_info]

def change_aspect_ratio(file_path, aspect_ratio):
    width, height = map(int, aspect_ratio.split(':'))
    output_path = os.path.splitext(file_path)[0] + '_changed_aspect.mp4'
    # 動画情報から元の解像度を取得
    probe = ffmpeg.probe(file_path)
    video_stream = next(stream for stream in probe["streams"] if stream['codec_type'] == 'video')
    iw = int(video_stream["width"])
    ih = int(video_stream["height"])

    # 元動画のアスペクト比
    input_aspect = iw / ih
    target_aspect = width / height

    # アスペクト比に合わせたパディングを計算
    if input_aspect > target_aspect:
        new_height = int(iw / target_aspect)
        pad_top_bottom = (new_height - ih) // 2
        pad_filter = f'pad={iw}:{new_height}:0:{pad_top_bottom}:black'
    else:
        new_width  =int(ih * target_aspect)
        pad_left_right = (new_width - iw) // 2
        pad_filter = f'pad={new_width}:{ih}:{pad_left_right}:0:black'

    aspect_filter = f'setsar=1, {pad_filter}'
    # 加工処理
    try:
        ffmpeg.input(file_path).output(output_path, vf=aspect_filter).run()
    except ffmpeg.Error as e:
        print(f'Failed to change aspect ratio: {str(e)}')
    
    video_info = ffmpeg.probe(output_path)

    return [output_path, video_info]

def extract_audio(file_path):
    output_path = os.path.splitext(file_path)[0] + 'extract_audio.mp3'
    try:
        ffmpeg.input(file_path).output(output_path, format='mp3').run()
    except ffmpeg.Error as e:
        print(f'Failed to extract audio: {str(e)}')

    audio_info = ffmpeg.probe(output_path)
    return [output_path, audio_info]

def convert_gif(file_path, split_time, type='gif'):
    start = split_time["start"]
    end = split_time["end"]
    output_path = os.path.splitext(file_path)[0] + f'conv_img.{type}'
    try:
        ffmpeg.input(file_path).filter('fps', fps=10, round='up').output(output_path, format=type, ss=start, t=end).run()
    except ffmpeg.Error as e:
        print(f'Failed to convert {type}: {str(e)}')

    gif_info = ffmpeg.probe(output_path)
    return [output_path, gif_info]
