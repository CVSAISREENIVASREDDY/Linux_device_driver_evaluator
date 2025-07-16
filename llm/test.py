import google.generativeai as genai
import os   
from dotenv import load_dotenv   

load_dotenv()

models = genai.list_models()
for model in models:
    print(model.name) 
genai.configure(api_key=os.getenv("API"))
