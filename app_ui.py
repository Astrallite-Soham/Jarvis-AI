import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import threading
import queue as _queue

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# ── Engine imports ─────────────────────────────────────────────────────────
try:
    import audio_engine
except Exception as _e:
    audio_engine = None
    print(f"[Jarvis] audio_engine unavailable: {_e}")

try:
    import dictionary_engine
except Exception as _e:
    dictionary_engine = None
    print(f"[Jarvis] dictionary_engine unavailable: {_e}")

try:
    import brain_engine
    brain_engine.init_if_needed()        # Pre-warm model on startup
except Exception as _e:
    brain_engine = None
    print(f"[Jarvis] brain_engine unavailable: {_e}")

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="J.A.R.V.I.S",
    page_icon="⬡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Session defaults ─────────────────────────────────────────────────────────
for _k, _v in {
    "jarvis_state":  "idle",
    "chat_history":  [],
    "mic_active":    False,
    "streaming_text": "",
    "is_streaming":  False,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg:       #030810;
    --surface:  #060f1c;
    --border:   #0d2544;
    --cyan:     #00d4ff;
    --cyan-dim: #004f6e;
    --green:    #00ffaa;
    --amber:    #ffaa00;
    --text:     #8ec8e8;
    --text-dim: #2a5070;
    --white:    #ddf0ff;
}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stBottom"],
section.main { background: var(--bg) !important; }

[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stBottom"]  { background: var(--bg) !important; border-top: 1px solid var(--border) !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--cyan-dim); border-radius: 2px; }

/* Global font */
*, p, label, div, span, li {
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--text);
}

/* Text input */
div[data-testid="stTextInput"] input {
    background:  var(--surface) !important;
    color:       var(--white)   !important;
    border:      1px solid var(--border) !important;
    border-radius: 3px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size:   13px !important;
    padding:     10px 14px !important;
    transition:  border 0.15s, box-shadow 0.15s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--cyan) !important;
    box-shadow:   0 0 12px rgba(0,212,255,0.25) !important;
    outline: none !important;
}

/* Buttons */
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stButton"] button {
    background:   transparent !important;
    color:        var(--cyan) !important;
    border:       1px solid var(--cyan-dim) !important;
    border-radius: 3px !important;
    font-family:  'JetBrains Mono', monospace !important;
    font-size:    12px !important;
    font-weight:  500 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding:      9px 14px !important;
    transition:   all 0.15s !important;
}
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stButton"] button:hover {
    border-color: var(--cyan) !important;
    background:   rgba(0,212,255,0.06) !important;
    box-shadow:   0 0 14px rgba(0,212,255,0.2) !important;
}

/* Containers */
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    background: var(--surface) !important;
}

/* Chat avatars — remove */
[data-testid="chatAvatarIcon-assistant"],
[data-testid="chatAvatarIcon-user"],
[data-testid="stChatMessageAvatarCell"],
.st-emotion-cache-janwst { display: none !important; }

/* Chat bubbles */
.jv-bubble {
    padding: 10px 15px;
    border-radius: 3px;
    margin-bottom: 8px;
    font-size: 13px;
    line-height: 1.6;
    border-left: 2px solid transparent;
    animation: fadeSlide 0.2s ease;
}
@keyframes fadeSlide {
    from { opacity:0; transform:translateY(4px); }
    to   { opacity:1; transform:translateY(0);   }
}
.jv-user {
    background: rgba(0, 212, 255, 0.04);
    border-color: var(--cyan);
    color: var(--white);
}
.jv-jarvis {
    background: rgba(0, 255, 170, 0.03);
    border-color: var(--green);
    color: #c8fff0;
}
.jv-system {
    background: rgba(255,170,0,0.04);
    border-color: var(--amber);
    color: #ffd988;
    font-style: italic;
    font-size: 11px;
}
.jv-label {
    font-size: 10px;
    letter-spacing: 2px;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 6px;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600;
}

/* Status strip */
.jv-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 10px;
    letter-spacing: 1.5px;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 6px;
}
.jv-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
.jv-dot-idle       { background: var(--cyan-dim);  box-shadow: 0 0 4px var(--cyan-dim); }
.jv-dot-processing { background: var(--amber);     box-shadow: 0 0 6px var(--amber); animation: blink 0.5s infinite; }
.jv-dot-active     { background: var(--green);     box-shadow: 0 0 6px var(--green); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* Header */
.jv-header {
    text-align: center;
    padding: 12px 0 4px;
}
.jv-title {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 30px;
    font-weight: 700;
    letter-spacing: 10px;
    color: var(--white) !important;
    text-shadow: 0 0 20px rgba(0,212,255,0.4);
}
.jv-subtitle {
    font-size: 9px;
    letter-spacing: 3px;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-top: 2px;
}

/* Scanning line overlay effect on the chat container */
.jv-scan::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    animation: scan 3s linear infinite;
    pointer-events: none;
}
@keyframes scan {
    from { top: 0; opacity: 0.6; }
    to   { top: 100%; opacity: 0; }
}
</style>
""", unsafe_allow_html=True)


# ── Arc Reactor ──────────────────────────────────────────────────────────────
def arc_reactor(state: str) -> None:
    palettes = {
        "idle":       ("#00d4ff", "#004f6e", "18s", "0.8s", "0.85"),
        "processing": ("#ffaa00", "#6e4400", "3s",  "0.4s", "0.95"),
        "active":     ("#00ffaa", "#006644", "1s",  "0.25s","1.0"),
    }
    c, dim, spd, pspd, op = palettes.get(state, palettes["idle"])

    html = f"""
<div style="display:flex;justify-content:center;align-items:center;height:220px;background:transparent;position:relative;">
  <!-- outer glow ring -->
  <div style="position:absolute;width:190px;height:190px;border-radius:50%;
    box-shadow:0 0 40px {c}22, 0 0 80px {c}11;"></div>
  <!-- dashed orbit -->
  <div style="position:absolute;width:170px;height:170px;border:1px dashed {c};
    border-radius:50%;opacity:0.18;animation:spin {spd} linear infinite;"></div>
  <!-- outer spinner -->
  <div style="position:absolute;width:150px;height:150px;
    border:2px solid transparent;border-top:2px solid {c};border-bottom:2px solid {c};
    border-radius:50%;animation:spin {spd} linear infinite;"></div>
  <!-- middle ring -->
  <div style="position:absolute;width:120px;height:120px;
    border:1px solid {dim};border-radius:50%;opacity:0.5;
    animation:spin {spd} linear infinite reverse;"></div>
  <!-- inner hex marks -->
  <div style="position:absolute;width:94px;height:94px;
    border:1px solid {c};border-radius:50%;opacity:0.3;
    animation:spin 8s linear infinite;"></div>
  <!-- core -->
  <div style="width:52px;height:52px;border-radius:50%;
    background:radial-gradient(circle, #ffffff 0%, {c} 45%, {dim} 100%);
    box-shadow:0 0 24px {c}, 0 0 48px {c}88;
    opacity:{op};animation:pulse {pspd} ease-in-out infinite;"></div>
</div>
<style>
@keyframes spin  {{ from{{transform:rotate(0deg)}} to{{transform:rotate(360deg)}} }}
@keyframes pulse {{
  0%,100%{{transform:scale(0.94);opacity:{float(op)*0.82:.2f}}}
  50%    {{transform:scale(1.06);opacity:{op}}}
}}
</style>"""
    components.html(html, height=220)


# ── Message renderer ─────────────────────────────────────────────────────────
def _render_msg(msg: dict) -> str:
    role = msg["role"]
    text = msg["text"]
    if role == "user":
        return f'<div class="jv-bubble jv-user"><span style="color:#00d4ff;font-size:10px;letter-spacing:2px;">YOU ▸ </span>{text}</div>'
    if role == "jarvis":
        return f'<div class="jv-bubble jv-jarvis"><span style="color:#00ffaa;font-size:10px;letter-spacing:2px;">JARVIS ▸ </span>{text}</div>'
    return f'<div class="jv-bubble jv-system">⚡ {text}</div>'


# ── Layout ───────────────────────────────────────────────────────────────────
st.markdown('<div class="jv-header"><div class="jv-title">J.A.R.V.I.S</div>'
            '<div class="jv-subtitle">Stark Industries · Cognitive Core v2.0</div></div>',
            unsafe_allow_html=True)

arc_reactor(st.session_state.jarvis_state)

# Status strip
state_cls = {
    "idle": "jv-dot-idle",
    "processing": "jv-dot-processing",
    "active": "jv-dot-active",
}.get(st.session_state.jarvis_state, "jv-dot-idle")

state_label = {
    "idle": "System nominal · awaiting command",
    "processing": "Processing ·  cognitive array active",
    "active": "Responding",
}.get(st.session_state.jarvis_state, "")

st.markdown(
    f'<div class="jv-status"><span class="jv-dot {state_cls}"></span>{state_label}</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="jv-label">Tactical feed</div>', unsafe_allow_html=True)

# Chat container — fixed height, scrollable
chat_box = st.container(height=300, border=True)

with chat_box:
    if not st.session_state.chat_history and not st.session_state.is_streaming:
        st.markdown(
            '<div style="color:var(--text-dim,#2a5070);text-align:center;'
            'margin-top:110px;font-size:11px;letter-spacing:2px;">'
            'COMM-LINK INACTIVE · AWAITING INPUT</div>',
            unsafe_allow_html=True,
        )
    for msg in st.session_state.chat_history:
        st.markdown(_render_msg(msg), unsafe_allow_html=True)

    # Live streaming placeholder — inside the scrollable container
    stream_ph = st.empty()
    if st.session_state.is_streaming and st.session_state.streaming_text:
        stream_ph.markdown(
            f'<div class="jv-bubble jv-jarvis">'
            f'<span style="color:#00ffaa;font-size:10px;letter-spacing:2px;">JARVIS ▸ </span>'
            f'{st.session_state.streaming_text}'
            f'<span style="opacity:0.4;animation:blink 0.6s infinite;">▌</span></div>',
            unsafe_allow_html=True,
        )


# ── Pipeline ─────────────────────────────────────────────────────────────────
def process_pipeline(user_query: str) -> None:
    """
    Full pipeline:
      1. Dictionary lookup (fast HTTP)
      2. Stream LLM sentence-by-sentence
      3. Speak each sentence the instant it's done — overlapping generation
    """
    user_query = user_query.strip()
    if not user_query:
        return

    # Commit user message
    st.session_state.chat_history.append({"role": "user", "text": user_query})
    st.session_state.jarvis_state = "processing"
    st.session_state.is_streaming = True
    st.session_state.streaming_text = ""

    # ── Step 1: Dictionary lookup ──────────────────────────────────────────
    dict_data = None
    if dictionary_engine and hasattr(dictionary_engine, "lookup"):
        try:
            result = dictionary_engine.lookup(user_query)
            if result and result.get("success"):
                dict_data = result
        except Exception:
            pass

    # ── Step 2 + 3: Stream LLM + sentence TTS in a background thread ───────
    full_reply = ""
    tts_q: _queue.Queue = _queue.Queue()

    def _tts_worker() -> None:
        """Consumes the TTS queue; runs in a daemon thread."""
        while True:
            item = tts_q.get()
            if item is None:
                return
            if audio_engine and hasattr(audio_engine, "speak_text"):
                try:
                    audio_engine.speak_text(item)
                except Exception:
                    pass

    tts_thread = threading.Thread(target=_tts_worker, daemon=True)
    tts_thread.start()

    try:
        if brain_engine and hasattr(brain_engine, "stream_sentences"):
            for sentence in brain_engine.stream_sentences(user_query, dict_data):
                full_reply += (" " if full_reply else "") + sentence

                # Update streaming display
                st.session_state.streaming_text = full_reply
                stream_ph.markdown(
                    f'<div class="jv-bubble jv-jarvis">'
                    f'<span style="color:#00ffaa;font-size:10px;letter-spacing:2px;">JARVIS ▸ </span>'
                    f'{full_reply}'
                    f'<span style="opacity:0.4;">▌</span></div>',
                    unsafe_allow_html=True,
                )

                # Queue sentence for TTS immediately
                tts_q.put(sentence)
        else:
            full_reply = "Sir, the brain_engine module is missing from this workspace."
    except Exception as e:
        full_reply = f"Cognitive array fault: {e}"

    # Signal TTS thread done
    tts_q.put(None)
    # Don't join — let audio finish in background while UI updates

    # ── Commit final reply ─────────────────────────────────────────────────
    full_reply = full_reply.strip() or "..."
    st.session_state.chat_history.append({"role": "jarvis", "text": full_reply})
    st.session_state.is_streaming = False
    st.session_state.streaming_text = ""
    st.session_state.jarvis_state = "idle"
    st.rerun()


from streamlit_mic_recorder import mic_recorder  # 🚀 Bring in browser recorder

# ── Input Dock ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Console Input Bridge</div>', unsafe_allow_html=True)
col_input, col_mic = st.columns([0.85, 0.15])

word = ""
send = False

with col_input:
    with st.form(key="input_form", clear_on_submit=True):
        word = st.text_input("Enter command or text query...", label_visibility="collapsed")
        send = st.form_submit_button("Send Command", use_container_width=True)

with col_mic:
    # 🌟 Browser audio capture button
    audio_data = mic_recorder(
        start_prompt="🎙️",
        stop_prompt="🛑",
        just_once=True,
        use_container_width=True,
        key="browser_mic"
    )

# ── Execution Handlers & Interlocking ─────────────────────────────────────────
if send and word.strip():
    st.session_state.mic_active = False
    process_pipeline(word)

# 🌐 Handle Browser Audio Stream Input
if audio_data and audio_data.get("bytes"):
    # Clear out audio data state instantly so it doesn't process on repeat loops
    raw_audio_bytes = audio_data["bytes"]
    st.session_state.jarvis_state = "active"
    
    # Send a status notice to the feed
    st.session_state.chat_history.append({"role": "system", "text": "Audio uplink established — processing transmission..."})
    
    # 🌟 To translate audio bytes into text in the cloud, we can pass it to Gemini!
    try:
        # We will create a helper function in brain_engine to handle this transcription
        if brain_engine and hasattr(brain_engine, "transcribe_audio_bytes"):
            voice_command = brain_engine.transcribe_audio_bytes(raw_audio_bytes)
            if voice_command and voice_command.strip():
                process_pipeline(voice_command)
            else:
                st.session_state.jarvis_state = "idle"
        else:
            st.session_state.chat_history.append({"role": "system", "text": "Cloud speech-to-text array unlinked."})
            st.session_state.jarvis_state = "idle"
    except Exception as e:
        st.session_state.chat_history.append({"role": "system", "text": f"Audio processing error: {str(e)}"})
        st.session_state.jarvis_state = "idle"

# ── Footer status ─────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;font-size:9px;letter-spacing:2px;'
    'color:#0d2544;margin-top:16px;">'
    'STARK INDUSTRIES · CLASSIFIED · COGNITIVE CORE v2.0</div>',
    unsafe_allow_html=True,
)
