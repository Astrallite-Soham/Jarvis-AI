import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI

class JarvisBrain:
    def __init__(self):
        self._llm = None
        self._prompt = None
        
    def _init_engine(self):
        # Check for Streamlit Cloud deployment key
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if api_key:
            # Cloud Execution Array
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", 
                google_api_key=api_key,
                temperature=0.3
            )
        else:
            # Local PC Fallback Execution Layout
            self._llm = OllamaLLM(model="phi3", temperature=0.3)
            
        # Behavior Profile
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

# Instantiate the global system core
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
    
    context_string = _brain_instance._format_dict_data(dict_data)
    
    try:
        # Chain the prompt template directly with our active model core
        chain = _prompt | _llm
        
        # Fire a stream call to get real-time tokens back from the cloud array
        response_stream = chain.stream({
            "context_block": context_string,
            "human_input": user_query
        })
        
        # Pull text blocks out of the live stream generation loop
        for chunk in response_stream:
            # Handle differences between LangChain community structures and Google structures
            text_content = chunk if isinstance(chunk, str) else getattr(chunk, "content", str(chunk))
            if text_content:
                yield text_content
                
    except Exception as e:
        yield f"Sir, an issue occurred within the cognitive relay logic: {str(e)}"
