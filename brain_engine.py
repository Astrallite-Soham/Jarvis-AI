import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI  # 🚀 Cloud Core Upgrade

class JarvisBrain:
    def __init__(self):
        self._llm = None
        self._prompt = None
        
    def _init_engine(self):
        # ── SYSTEM INTELLIGENCE CHECK ──────────────────────────────────────────
        # If running on Streamlit Cloud, look for the secure environment secret.
        # Otherwise, look for a local environment variable.
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if api_key:
            # 🌐 PRODUCTION MODE: Run at lightning speed using Google's Cloud Array
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", 
                google_api_key=api_key,
                temperature=0.3
            )
        else:
            # 💻 LOCAL FALLBACK: Fallback to your laptop's Phi-3 model if offline
            self._llm = OllamaLLM(model="phi3", temperature=0.3)
            
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

# Global core instantiation for the UI pipeline to hook into
_brain_instance = JarvisBrain()
_brain_instance._init_engine()
_llm = _brain_instance._llm
_prompt = _brain_instance._prompt

# 🌟 UI INTERLOCK FIX
# This empty function acts as a buffer so app_ui.py doesn't throw an AttributeError
def init_if_needed():
    pass
