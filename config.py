import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize the LangChain Chat model with Groq
sky_ai = ChatGroq(api_key=GROQ_API_KEY, 
               model_name="llama-3.3-70b-versatile", 
               temperature=0.2,
               max_tokens=500)