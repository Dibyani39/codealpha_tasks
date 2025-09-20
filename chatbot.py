import streamlit as st
st.set_page_config(page_title="📦 Chatbot for FAQs", page_icon="🤖", layout="centered")

import pandas as pd
import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
import nltk
from gtts import gTTS
import tempfile
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode

# ----------------- STOPWORDS -----------------
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

# ----------------- SYNONYM DICTIONARY -----------------
synonyms = {
    "guarantee": "warranty",
    "ship": "delivery",
    "send": "delivery",
    "return": "refund",
    "purchase": "buy",
    "cost": "price",
    "cheap": "price",
    "money back": "refund",
    "cash on delivery": "COD"
}

def replace_synonyms(text):
    for word, replacement in synonyms.items():
        text = re.sub(rf"\b{word}\b", replacement, text, flags=re.IGNORECASE)
    return text

# ----------------- PREPROCESSING FUNCTION -----------------
def preprocess(text):
    text = text.lower()
    text = replace_synonyms(text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = re.findall(r"\b\w+\b", text)
    tokens = [word for word in tokens if word not in stop_words]
    return " ".join(tokens)

# ----------------- LOAD FAQ DATA -----------------
@st.cache_data
def load_data():
    df = pd.read_csv("faqs.csv")
    df["clean_question"] = df["question"].apply(preprocess)
    return df

faq_df = load_data()

# ----------------- TF-IDF MODEL -----------------
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(faq_df["clean_question"])

def get_answer(user_input):
    user_input_clean = preprocess(user_input)
    user_vec = vectorizer.transform([user_input_clean])
    similarity = cosine_similarity(user_vec, X)
    idx = similarity.argmax()
    score = similarity[0, idx]
    if score < 0.2:
        return "❌ Sorry, I don't have an answer for that."
    return faq_df.iloc[idx]["answer"]

# ----------------- STREAMLIT UI -----------------
st.title("🤖 Chatbot for FAQs")
st.write("You can ask your question by typing or speaking directly!")

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [("Bot", "👋 Hello! I’m your Product FAQ Assistant. Ask me anything about our products!")]

# ----------------- Text Input -----------------
text_input = st.text_input("Type your question:")

if st.button("Ask") and text_input.strip() != "":
    user_question = text_input
    answer = get_answer(user_question)
    st.session_state["messages"].append(("You", user_question))
    st.session_state["messages"].append(("Bot", answer))

# ----------------- Voice Input -----------------
st.write("Or speak your question:")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.transcribed_text = None

    def recv_audio(self, frame):
        audio_data = frame.to_ndarray()
        return frame

webrtc_ctx = webrtc_streamer(
    key="voice-chatbot",
    mode=WebRtcMode.SENDRECV,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True
)

if webrtc_ctx.state.playing:
    st.info("🎤 Speak now...")

if webrtc_ctx.audio_receiver:
    frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
    if frames:
        # Convert audio frames to WAV for recognition
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
            tmp_wav.write(frames[0].to_bytes())
            tmp_wav.flush()
            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_wav.name) as source:
                audio = recognizer.record(source)
                try:
                    user_question = recognizer.recognize_google(audio)
                    st.info(f"🎤 You said: {user_question}")
                    answer = get_answer(user_question)
                    st.session_state["messages"].append(("You", user_question))
                    st.session_state["messages"].append(("Bot", answer))
                except:
                    st.warning("⚠️ Could not understand the audio.")

# ----------------- Display Chat -----------------
for sender, msg in st.session_state["messages"]:
    if sender == "You":
        st.markdown(f"🧑 **{sender}:** {msg}")
    else:
        st.markdown(f"🤖 **{sender}:** {msg}")
        # Voice response
        tts = gTTS(text=msg, lang="en")
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            tts.save(f"{fp.name}.mp3")
            st.audio(f"{fp.name}.mp3", format="audio/mp3")
