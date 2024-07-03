import praw
import random
import whisper
import os
import string
import ffmpeg
from pytube import YouTube
from pydub import AudioSegment
from gtts import gTTS


def santizie_text(text):
    return ''.join(char for char in text if char not in string.punctuation)
def get_random_hot_post(subreddit_name):
    reddit = praw.Reddit(client_id='ADKTOWjCN3nK6pJP32OCPQ',
                         client_secret='49Hg3Ml5UxSapXVyPqRkivfaB6-rfg',
                         user_agent='iphone')

    subreddit = reddit.subreddit(subreddit_name)
    hot_posts = list(subreddit.hot(limit=None)) 
    if not hot_posts:
        return None
    random_post = random.choice(hot_posts)  
    return random_post.title, random_post.selftext
def text_to_speech(text, filename, lang='en', slow=False):
    tts = gTTS(text=text, lang=lang, slow=slow)
    filename = filename + ".mp3"
    tts.save(filename)
    return filename
def caption_with_duration(filename):
    model = whisper.load_model('base')
    result = model.transcribe(filename, language="en", word_timestamps=True)

    captions = []
    index = 1

    for segment in result['segments']:
        for word in segment['words']:
            word_text = word['word']
            start_time = word['start']
            end_time = word['end']

            # Convert time to milliseconds
            start_time_ms = int(start_time * 1000)
            end_time_ms = int(end_time * 1000)

            # Manually format the timestamp in HH:MM:SS,MS format
            start_time_formatted = "{:02d}:{:02d}:{:02d},{}".format(
                start_time_ms // 3600000,
                (start_time_ms % 3600000) // 60000,
                (start_time_ms % 60000) // 1000,
                start_time_ms % 1000
            )
            end_time_formatted = "{:02d}:{:02d}:{:02d},{}".format(
                end_time_ms // 3600000,
                (end_time_ms % 3600000) // 60000,
                (end_time_ms % 60000) // 1000,
                end_time_ms % 1000
            )

            # Format caption line
            caption_line = f"{index}\n{start_time_formatted} --> {end_time_formatted}\n{word_text}\n\n"
            captions.append(caption_line)
            index += 1

    # Write captions to an SRT file
    srt_filename = os.path.splitext(filename)[0] + ".srt"
    with open(srt_filename, 'w') as srt_file:
        srt_file.writelines(captions)

    print(f"Captions written to {srt_filename}")
def add_subtitles_to_video(input_video_path, subtitle_file_path, output_video_path):
    (
        ffmpeg
        .input(input_video_path)
        .output(output_video_path, vf=f'subtitles={subtitle_file_path}:force_style=\'Alignment=10\'')
        .run()
    )
def trim_video(input_video_path, output_video_path, start_time, end_time):
    (
        ffmpeg
        .input(input_video_path, ss=start_time)  # ss specifies start time
        .output(output_video_path, to=end_time)  # to specifies duration (end time - start time)
        .run()
    )
def get_audio_duration(audio_file_paths):
    total_duration = 0.0

    for audio_file_path in audio_file_paths:
        probe = ffmpeg.probe(audio_file_path)
        audio_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        if audio_info:
            duration = float(audio_info['duration'])
            total_duration += duration

    return total_duration  # Return total duration in secondsr
def download_youtube_video(youtube_url, output_path='./'):
    try:
        yt = YouTube(youtube_url)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if video:
            print(f'Downloading "{yt.title}"...')
            video.download(output_path, 'background.mp4')
            print('Download completed.')
        else:
            print(f'Video "{yt.title}" is not available for download.')
    except Exception as e:
        print(f'Error downloading video: {str(e)}')
def combine_audio_files(file1_path: str, file2_path: str, output_path: str):
    try:
        # Load the audio files
        audio1 = AudioSegment.from_file(file1_path)
        audio2 = AudioSegment.from_file(file2_path)

        # Combine the audio files
        combined_audio = audio1 + audio2

        # Export the combined audio to the output path
        combined_audio.export(output_path, format="mp3")

        print("Audio files combined successfully!")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Audio file not found: {e}")
    except Exception as e:
        raise Exception(f"Error combining audio files: {e}")
def combine_audio_and_video(video_file_path, audio_file_path, output_file_path):
    video_stream = ffmpeg.input(video_file_path)
    audio_stream = ffmpeg.input(audio_file_path)
    ffmpeg.output(video_stream, audio_stream, output_file_path).run()


title, content = get_random_hot_post('amItheasshole')
title = santizie_text(title)
content = santizie_text(content)
text_to_speech(content, 'content')
text_to_speech(title, 'title')
combine_audio_files('title.mp3', 'content.mp3', 'final.mp3')
audio_duration = get_audio_duration(['final.mp3'])
download_youtube_video('https://www.youtube.com/watch?v=7yl7Wc1dtWc')
trim_video('background.mp4', 'trimmed.mp4', 0, audio_duration)
caption_with_duration('final.mp3')
add_subtitles_to_video('trimmed.mp4', 'final.srt', 'final_video.mp4')
combine_audio_and_video('final_video.mp4', 'final.mp3', 'final.mp4')

os.remove('content.mp3')
os.remove('title.mp3')
os.remove('trimmed.mp4')
os.remove('background.mp4')
os.remove('final.mp3')
os.remove('final_video.mp4')
os.remove('final.srt')
