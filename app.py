
import io
import streamlit as st
from gtts import gTTS
from deep_translator import GoogleTranslator

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="🌐 Language Translation Tool",
    page_icon="🌐",
    layout="centered"
)

# ----------------- TITLE + CAPTION -----------------
st.markdown(
    """
    <h1 class="bounce-title">🌐 Language Translation Tool</h1>
    <p class="glow-caption">Instantly translate text between multiple languages with speech support</p>

    <style>
    /* Bounce animation for heading */
    .bounce-title {
        text-align: center;
        font-size: 42px;
        animation: bounce 1.5s ease forwards;
        color: #E70773;
        margin-bottom: 5px;
    }
    @keyframes bounce {
        0%   { transform: translateY(-50px); opacity: 0; }
        50%  { transform: translateY(10px); opacity: 1; }
        70%  { transform: translateY(-5px); }
        100% { transform: translateY(0); }
    }

    /* Glow effect for caption */
    .glow-caption {
        text-align: center;
        font-size: 18px;
        color: #FF9800;
        animation: fadeIn 2s ease forwards, glow 2s ease-in-out infinite alternate;
        animation-delay: 1.5s; /* wait until bounce finishes */
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes glow {
        from { text-shadow: 0 0 5px #FF9800, 0 0 10px #FF5722; }
        to   { text-shadow: 0 0 20px #FFC107, 0 0 30px #FF5722; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------- SESSION STATE -----------------
if "src" not in st.session_state:
    st.session_state.src = "English"
if "tgt" not in st.session_state:
    st.session_state.tgt = "Hindi (हिन्दी)"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ----------------- DARK/LIGHT MODE -----------------
def apply_theme():
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
            body {
                background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #1e3c72);
                background-size: 400% 400%;
                animation: gradient 15s ease infinite;
                color: white;
            }
            @keyframes gradient {
                0% {background-position: 0% 50%;}
                50% {background-position: 100% 50%;}
                100% {background-position: 0% 50%;}
            }
            .stTextArea textarea {
                background-color: #2b2b2b;
                color: white;
                border-radius: 10px;
                transition: all 0.3s ease-in-out;
            }
            div[data-testid="stSidebar"] {
                background: linear-gradient(135deg, #141E30, #243B55);
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <style>
            body {
                background: linear-gradient(-45deg, #fdfbfb, #ebedee, #dfe9f3, #ffffff);
                background-size: 400% 400%;
                animation: gradient 15s ease infinite;
                color: black;
            }
            @keyframes gradient {
                0% {background-position: 0% 50%;}
                50% {background-position: 100% 50%;}
                100% {background-position: 0% 50%;}
            }
            .stTextArea textarea {
                background-color: #ffffff;
                color: black;
                border-radius: 10px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease-in-out;
            }
            div[data-testid="stSidebar"] {
                background: linear-gradient(135deg, #E0EAFC, #CFDEF3);
                color: black;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

apply_theme()

# ----------------- LANGUAGE OPTIONS -----------------
LANGUAGES = {
    "Auto-detect": "auto",
    "English": "en",
    "Hindi (हिन्दी)": "hi",
    "Bengali (বাংলা)": "bn",
    "Tamil (தமிழ்)": "ta",
    "Telugu (తెలుగు)": "te",
    "Marathi (मराठी)": "mr",
    "Gujarati (ગુજરાતી)": "gu",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Malayalam (മലയാളം)": "ml",
    "Urdu (اردو)": "ur",
    "Spanish (Español)": "es",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Portuguese (Português)": "pt",
    "Italian (Italiano)": "it",
    "Russian (Русский)": "ru",
    "Arabic (العربية)": "ar",
    "Chinese (简体中文)": "zh-CN",
    "Japanese (日本語)": "ja",
    "Korean (한국어)": "ko"
}

# ----------------- SIDEBAR -----------------
st.sidebar.header("⚙️ Settings")

st.sidebar.checkbox("🌗 Dark Mode", key="dark_mode", on_change=apply_theme)

col1, col2 = st.sidebar.columns(2)

with col1:
    src_label = st.selectbox("Source", list(LANGUAGES.keys()),
                             index=list(LANGUAGES.keys()).index(st.session_state.src))
    st.session_state.src = src_label

with col2:
    tgt_label = st.selectbox("Target", list(LANGUAGES.keys()),
                             index=list(LANGUAGES.keys()).index(st.session_state.tgt))
    st.session_state.tgt = tgt_label

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("🔄 Swap", use_container_width=True):
    st.session_state.src, st.session_state.tgt = st.session_state.tgt, st.session_state.src
    st.rerun()

src_code = LANGUAGES[st.session_state.src]
tgt_code = LANGUAGES[st.session_state.tgt]

# ----------------- BUTTON STYLING -----------------
st.markdown("""
<style>
div[data-testid="stSidebar"] button {
    background-color: #4CAF50;
    color: white;
    border-radius: 12px;
    font-size: 16px;
    padding: 8px;
    transition: all 0.3s ease;
}
div[data-testid="stSidebar"] button:hover {
    background-color: #45a049;
    transform: scale(1.08);
}
button[kind="primary"] {
    background: linear-gradient(90deg, #ff6a00, #ee0979);
    color: white !important;
    font-size: 18px;
    border-radius: 12px !important;
    padding: 10px !important;
    transition: all 0.3s ease-in-out;
}
button[kind="primary"]:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 15px rgba(255,105,180,0.6);
}
</style>
""", unsafe_allow_html=True)

# ----------------- TEXT INPUT -----------------
text = st.text_area("✍️ Enter text to translate", height=150, placeholder="Type or paste your text here...")

# ----------------- TRANSLATION -----------------
translated_text = ""

if st.button("🚀 Translate", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("⚠️ Please enter some text to translate.")
    else:
        try:
            translated_text = GoogleTranslator(source=src_code, target=tgt_code).translate(text)
        except Exception as e:
            st.error(f"❌ Translation failed: {e}")

# ----------------- DISPLAY RESULT -----------------
if translated_text:
    st.markdown(
        f"""
        <div style="animation: fadeIn 1.5s;">
        <h3>✅ Translated Text</h3>
        </div>
        <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.text_area("Result", value=translated_text, height=150)

    with st.expander("🔊 Listen to Translation"):
        try:
            tts = gTTS(text=translated_text, lang=tgt_code if tgt_code != "auto" else "en")
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.audio(buf, format="audio/mp3")
        except Exception:
            st.info("TTS not available for this language.")
