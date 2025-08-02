import re 
import os 
import sys 
from dotenv import load_dotenv 
load_dotenv() 
import json 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 
from llm.model import GeminiModel 

model = GeminiModel(api_key=os.getenv("API")) 

class GetResponses:
    
    def __init__(self):
        pass 
    
    def generate_code(self,prompt : str):
        """
        Generates C code using all available Gemini models for each prompt.
        Returns a list of dictionaries with the model name and generated code.
        """
        print(f"models are generating responses for prompt ") 
        return model._generate_code_per_prompt(prompt)  
    
if __name__ == "__main__": 
    
    responser = GetResponses() 
    sample_prompts = [
        "Write a Linux kernel driver for a simple device.",
        "2Implement a character device driver with basic read/write operations.",
        "Create a kernel module that interacts with hardware."
    ]

    all_prompt_responses = {} 
    for prompt in sample_prompts:
        all_prompt_responses[prompt] = responser.generate_code(prompt)  

    with open("all_prompt_responses.json", "w") as f:
        json.dump(all_prompt_responses, f, indent=4) 