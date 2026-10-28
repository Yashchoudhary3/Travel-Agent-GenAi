from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_retries=3,
)