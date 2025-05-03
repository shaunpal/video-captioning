import whisper
import os
import ffmpeg
import asyncio
import streamlit as st
from whisper.utils import get_writer
from tempfile import NamedTemporaryFile
from googletrans import Translator

SUPPORTED_LANGUAGES = {
    'afrikaans': 'af',
    'albanian': 'sq',
    'amharic': 'am',
    'arabic': 'ar',
    'armenian': 'hy',
    'azerbaijani': 'az',
    'basque': 'eu',
    'belarusian': 'be',
    'bengali': 'bn',
    'bosnian': 'bs',
    'bulgarian': 'bg',
    'catalan': 'ca',
    'cebuano': 'ceb',
    'chichewa': 'ny',
    'chinese (simplified)': 'zh-cn',
    'chinese (traditional)': 'zh-tw',
    'corsican': 'co',
    'croatian': 'hr',
    'czech': 'cs',
    'danish': 'da',
    'dutch': 'nl',
    'english': 'en',
    'esperanto': 'eo',
    'estonian': 'et',
    'filipino': 'tl',
    'finnish': 'fi',
    'french': 'fr',
    'frisian': 'fy',
    'galician': 'gl',
    'georgian': 'ka',
    'german': 'de',
    'greek': 'el',
    'gujarati': 'gu',
    'haitian creole': 'ht',
    'hausa': 'ha',
    'hawaiian': 'haw',
    'hebrew': 'he',
    'hindi': 'hi',
    'hmong': 'hmn',
    'hungarian': 'hu',
    'icelandic': 'is',
    'igbo': 'ig',
    'indonesian': 'id',
    'irish': 'ga',
    'italian': 'it',
    'japanese': 'ja',
    'javanese': 'jw',
    'kannada': 'kn',
    'kazakh': 'kk',
    'khmer': 'km',
    'korean': 'ko',
    'kurdish (kurmanji)': 'ku',
    'kyrgyz': 'ky',
    'lao': 'lo',
    'latin': 'la',
    'latvian': 'lv',
    'lithuanian': 'lt',
    'luxembourgish': 'lb',
    'macedonian': 'mk',
    'malagasy': 'mg',
    'malay': 'ms',
    'malayalam': 'ml',
    'maltese': 'mt',
    'maori': 'mi',
    'marathi': 'mr',
    'mongolian': 'mn',
    'myanmar (burmese)': 'my',
    'nepali': 'ne',
    'norwegian': 'no',
    'odia': 'or',
    'pashto': 'ps',
    'persian': 'fa',
    'polish': 'pl',
    'portuguese': 'pt',
    'punjabi': 'pa',
    'romanian': 'ro',
    'russian': 'ru',
    'samoan': 'sm',
    'scots gaelic': 'gd',
    'serbian': 'sr',
    'sesotho': 'st',
    'shona': 'sn',
    'sindhi': 'sd',
    'sinhala': 'si',
    'slovak': 'sk',
    'slovenian': 'sl',
    'somali': 'so',
    'spanish': 'es',
    'sundanese': 'su',
    'swahili': 'sw',
    'swedish': 'sv',
    'tajik': 'tg',
    'tamil': 'ta',
    'telugu': 'te',
    'thai': 'th',
    'turkish': 'tr',
    'ukrainian': 'uk',
    'urdu': 'ur',
    'uyghur': 'ug',
    'uzbek': 'uz',
    'vietnamese': 'vi',
    'welsh': 'cy',
    'xhosa': 'xh',
    'yiddish': 'yi',
    'yoruba': 'yo',
    'zulu': 'zu'
}

def extract_audio_and_generate_subtitles(video_file, desired_language, subtitle_format="srt"):
    # Load Whisper model
    st.write("Loading the base model...")
    model = whisper.load_model('base')

    # Translate transcription to target language
    st.write("Transcribing video file...")
    result = model.transcribe(video_file.name, fp16=False)
    detected_language = result['language']
    st.write(f"Detected video language: {detected_language}")

    target_language = SUPPORTED_LANGUAGES.get(desired_language, 'en')
    if detected_language != target_language:
        st.write(f"Translating transcripts to '{'english' if target_language == 'en' else desired_language}'...")
        asyncio.run(translate_text(result, target_language))

    # Create a temporary subtitle file for writing
    temp_subtitle_file = NamedTemporaryFile('w+', delete=False, suffix=f'.{subtitle_format}')

    # Write the subtitles to the temporary file
    st.write("Generating caption...")
    sub_writer = get_writer(subtitle_format, os.path.dirname(temp_subtitle_file.name))
    sub_writer(result, temp_subtitle_file.name)

    return temp_subtitle_file


def embed_subtitles_to_video(video_file, subtitle_file):
    # Create a temporary video file for writing
    video_file_output = NamedTemporaryFile(delete=False, suffix=".mp4")

    # Use ffmpeg to embed subtitles into the video
    st.write("Embedding subtitles to video...")
    ffmpeg.input(video_file.name).output(video_file_output.name, vf=f"subtitles={subtitle_file.name}").run(overwrite_output=True)

    # Delete the video and subtitle files
    temp_video_file_output = create_deletable_temp_copy_and_remove_file(video_file_output, "mp4", "wb+")
    temp_subtitle_file_output = create_deletable_temp_copy_and_remove_file(subtitle_file, "srt", "w+")
    return temp_video_file_output, temp_subtitle_file_output


def create_deletable_temp_copy_and_remove_file(original_file, temp_file_extension, temp_file_mode):
    # Create a temporary file
    temp_file = NamedTemporaryFile(temp_file_mode, delete=True, suffix=f".{temp_file_extension}")
    read_mode = 'r' if temp_file_mode == 'w+' else 'rb'
    with open(original_file.name, read_mode) as f:
        temp_file.write(f.read())
    os.remove(original_file.name)
    return temp_file


async def translate_text(transcribed_result, target_language):
    translator = Translator()
    for segment in transcribed_result['segments']:
        translated = await translator.translate(segment['text'], dest=target_language)
        if hasattr(translated, 'text'):
            segment['text'] = translated.text


def process_video(video_file, desired_language):
    # Step 1: Generate subtitles
    subtitle_file = extract_audio_and_generate_subtitles(video_file, desired_language)

    # Step 2: Embed subtitles into the video and return both files
    video_file_output, subtitle_file_output = embed_subtitles_to_video(video_file, subtitle_file)

    return video_file_output, subtitle_file_output