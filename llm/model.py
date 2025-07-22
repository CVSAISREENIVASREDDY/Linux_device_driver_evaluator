import google.generativeai as genai
import os
from dotenv import load_dotenv   
import re

models = [
    "gemini-1.5-flash",
    "gemini-2.5-flash",
]


class GeminiModel:

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)

    def _generate_code_per_prompt(self, prompt: str):
        """
        Generates C code using all available Gemini models and collects every output.
        """


        system_instruction = (
            "You are an expert Linux kernel developer. Generate clean, production-quality "
            "Linux device driver code in C that strictly adheres to kernel coding standards. "
            "Ensure proper module structure, error handling, and memory management. "
            "Output only valid C code — no explanations, comments, or markdown formatting."
            "don't give any markup, the code should be convertible to makefile easily"
        )

        output = {}

        for model_name in models: 
            try:
                model = genai.GenerativeModel(
                    model_name,
                    system_instruction=system_instruction
                )

                response = model.generate_content(
                    prompt
                )
                if response.text:
                    output[model_name] = {
                        "success" : True,
                        "code" : response.text,
                    }
                else:
                    reason = response.candidates[0].finish_reason if response.candidates else "Unknown"
                    error_message = f"Model {model_name} produced an empty response. Finish Reason: {reason}"
                    print(error_message)
                    output[model_name] = {
                        "success" : False,
                        "code" : error_message,
                    }

            except Exception as e:
                error_message = f"Model {model_name} failed with an error: {e}"
                print(error_message)
                output[model_name] = {
                        "success" : False,
                        "code" : error_message,
                    }
        
        return output 
