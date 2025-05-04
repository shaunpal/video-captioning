import streamlit as st
import requests
import os
from urllib.parse import quote
from tempfile import NamedTemporaryFile
from processor import process_video, TEMP_FOLDER_DIR
from dotenv import load_dotenv

load_dotenv()
YT_API_HOSTNAME = os.environ.get("YT_API_HOSTNAME")

def get_youtube_video(_url):
    if not _url:
        return
    try:
        resp = requests.get(f"{YT_API_HOSTNAME}/get-youtube-video?url={quote(str(_url))}")
        st.session_state["data"] = resp.json()
    except requests.exceptions.RequestException:
        st.error("Unable to retrieving YouTube video, try again later..")


vid_caption, you_extract, live_caption = st.tabs(["Embed video caption", "Extract youtube video", "Live captioning - COMING SOON"])

with vid_caption:
    st.title("Embed video captions")
    st.write(
        """
        Upload any video of your liking and embed captions/subtitles. Enjoy!
        """
    )
    chosen_language = st.selectbox("Select your choice of caption language",
                                   ("English", "Chinese", "Spanish", "Japanese"),
                                   placeholder="Select language...")

    with st.form('video_upload'):
        video_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"], accept_multiple_files=False)
        vid_temp = NamedTemporaryFile(dir=TEMP_FOLDER_DIR, delete=True, suffix='.mp4')
        submitted = st.form_submit_button("Upload")
        if submitted:
            contents = video_file.read()
            vid_temp.write(contents)
            with st.status("Processing the video...", expanded=True):
                output_video_temp_file, output_subtitle_temp_file = process_video(vid_temp, chosen_language.lower())
                st.balloons()

                with open(output_video_temp_file.name, 'rb') as video_temp_file:
                    st.video(video_temp_file.read(), subtitles=f"{output_subtitle_temp_file.name}")

with (you_extract):
    st.title("YouTube video extractor")
    st.write(
        """ 
        Extract and download any video from YouTube. Enjoy!
        """
    )

    st.session_state["youtube_url"] = st.text_input(
        "YouTube Url",
        placeholder="Paste YouTube link here..",
    )
    if "data" not in st.session_state:
        st.session_state["data"] = None


    st.button("Search", on_click=get_youtube_video, args=(st.session_state["youtube_url"],))

    if st.session_state['data']:
        st.success("Video found and collected")
        with st.expander("Formats available"):
            audios = st.session_state['data']['audios']
            videos = st.session_state['data']['videos']
            st.write(f"# {st.session_state['data']['title']}")
            st.image(image=st.session_state['data']['thumbnail'])
            st.write(f"<b>Duration:</b> {st.session_state['data']['video_duration']}", unsafe_allow_html=True)
            st.write("## Video")
            for data in videos:
                st.write("""
                    <div style="display: flex; justify-content: space-between;">
                        <div><b>\tFormat: \t</b>""" + data['video_format'] + """</div>
                        <div>\t<a href='""" + data['video_url'] + """'>Download</a></div>
                    </div>
                """, unsafe_allow_html=True)

            st.write("## Audio")
            for data in audios:
                st.write("""
                    <div style="display: flex; justify-content: space-between;">
                        <div><b>\tFormat: \t</b>""" + data['audio_format'] + """</div>
                        <div><a href='""" + data['audio_url'] + """'>Download</a></div>
                    </div>
                """, unsafe_allow_html=True)


with live_caption:
    st.write("""
        Live captioning is coming soon. Stay tuned!
    """)