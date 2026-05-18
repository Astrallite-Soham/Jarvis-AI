import os
import base64
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

class JarvisBrain:
    def __init__(self):
        self._llm = None
        self._prompt = None
        
    def _init_engine(self):
        # 🔑 Look for the secure cloud secret key
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if api_key:
            # 🌐 PRODUCTION MODE: Google Cloud Array execution
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=api_key,
                temperature=0.3
            )
        else:
            # 🛑 FALLBACK ALERT
            self._llm = None
            
        # ── JARVIS BEHAVIOR DIRECTIVE ──────────────────────────────────────────
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are J.A.R.V.I.S., Tony Stark's sophisticated, highly advanced artificial intelligence. "
                "Your tone is British, elegant, polite, deeply loyal, yet subtly witty. "
                "Address the user exclusively as 'Sir'. Keep your answers exceptionally concise, "
                "technically sharp, and beautifully formatted using clean text.\n\n"
                "Linguistic Tactical Context:\n{context_block}"
            )),
            ("human", "{human_input}")
        ])

    def _format_dict_data(self, dict_payload):
        if not dict_payload:
            return "No auxiliary data found in local data banks."
        return str(dict_payload)

# Initialize the clean global system core
_brain_instance = JarvisBrain()
_brain_instance._init_engine()
_llm = _brain_instance._llm
_prompt = _brain_instance._prompt

# ── REQUIRED UI PIPELINE INTERLOCKS (MUST BE LEFT-FLUSH) ────────────────────

def init_if_needed():
    """Keeps app_ui.py initialization sequence from crashing."""
    pass

def stream_sentences(user_query: str, dict_data: dict = None):
    """Processes the prompt, calls the LLM pipeline, and yields the response."""
    global _llm, _prompt, _brain_instance
    if not _llm:
        yield "Sir, the Google cloud synchronization key is missing."
        return
        
    context_string = _brain_instance._format_dict_data(dict_data)
    try:
        chain = _prompt | _llm
        response_stream = chain.stream({
            "context_block": context_string,
            "human_input": user_query
        })
        for chunk in response_stream:
            text_content = chunk if isinstance(chunk, str) else getattr(chunk, "content", str(chunk))
            if text_content:
                yield text_content
    except Exception as e:
        yield f"Sir, an issue occurred within the cognitive relay logic: {str(e)}"

def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Sends raw audio bytes from browser directly to Gemini for transcription."""
    global _llm
    if not _llm:
        return "Audio link failure: Engine core uninitialized."
        
    try:
        # LangChain's ChatGoogleGenerativeAI parses multimedia via base64 data URIs
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        audio_content = {
            "type": "media_url",
            "media_url": f"data:audio/wav;base64,{b64_audio}"
        }
        
        prompt_message = {
            "type": "text",
            "text": "You are a highly accurate speech-to-text system. Transcribe the spoken audio stream exactly as stated. Do not add metadata, comments, or summaries. Output the transcription directly."
        }
        
        # Dispatch structured payload message contents
        response = _llm.invoke([[prompt_message, audio_content]])
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        return f"Transcription engine failure: {str(e)}"
