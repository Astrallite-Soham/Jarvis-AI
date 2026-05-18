import os
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
                model="gemini-2.5-flash",  # 🌟 UPGRADED ENGINE
                google_api_key=api_key,
                temperature=0.3
            )
        else:
            # 🛑 CRITICAL FALLBACK ALERT
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

# ── REQUIRED UI PIPELINE INTERLOCKS ──────────────────────────────────────────

def init_if_needed():
    """Keeps app_ui.py initialization sequence from crashing."""
    pass

def stream_sentences(user_query: str, dict_data: dict = None):
    """
    Processes the prompt, calls the LLM pipeline, and yields the response 
    back to the app_ui.py text streamer window.
    """
    global _llm, _prompt, _brain_instance
    
    # Safety guard if the secret key was skipped or missing entirely
    if not _llm:
        yield "Sir, the Google cloud synchronization key is missing. Please check your Streamlit app environment configuration."
        return
        
    context_string = _brain_instance._format_dict_data(dict_data)
    
    try:
        # Chain the prompt template directly with our active model core
        chain = _prompt | _llm
        
        # Fire a stream call to get real-time tokens back from the cloud array
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
    """
    Sends raw audio bytes from the user's browser directly to Gemini
    to turn speech into a text string command.
    """
    global _llm
    if not _llm:
        return ""
        
    try:
        # Format raw audio structure payload for the Google GenAI payload wrapper
        audio_payload = {
            "mime_type": "audio/wav",
            "data": audio_bytes
        }
        
        # Call Gemini with an explicit translation request directive
        prompt = "You are a speech-to-text system. Transcribe the audio exactly as spoken, without adding commentary."
        response = _llm.invoke([prompt, audio_payload])
        
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"Transcription failure: {e}")
        return ""
