import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY="Gemini_API_Key"
api_key=os.getenv(API_KEY)
client=genai.Client(api_key=api_key)
def generate_response(prompt):
    
    if not prompt or not prompt.strip():
        
        raise ValueError("prompt cannot be empty")
    
    response=client.models.generate_content(model="gemini-3.5-flash-lite",contents=prompt)
    
    return response.text
    

    