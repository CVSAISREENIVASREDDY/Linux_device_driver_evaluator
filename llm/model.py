import google.generativeai as genai
import os   
from dotenv import load_dotenv   

# load_dotenv()
# genai.configure(api_key=os.getenv("API")) 

# models = genai.list_models() 

models = [
    "gemini-1.5-flash",
    "gemini-2.5-flash",
]


class GeminiModel:

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
    

    def generate_code(self, prompts):
        """
        Generates C code using all available Gemini models for each prompt.
        Returns a list of dictionaries with the model name and generated code.
        """
        outputs = {}
        for prompt in prompts:
            outputs[prompt] = self._generate_code_per_prompt(prompt)
        return outputs
                      


    def _generate_code_per_prompt(self, prompt: str):
        """
        Generates C code using all available Gemini models and collects every output.
        """


        system_instruction = (
            "You are an expert Linux kernel developer. Generate clean, production-quality "
            "Linux device driver code in C that strictly adheres to kernel coding standards. "
            "Ensure proper module structure, error handling, and memory management. "
            "Output only valid C code — no explanations, comments, or markdown formatting."
        )


        outputs = []

        for model_name in models:
            try:
                # print(f"Attempting code generation with model: {model_name}")
                model = genai.GenerativeModel(
                    model_name,
                    system_instruction=system_instruction
                )

                response = model.generate_content(
                    prompt
                )
                if response.text:
                    outputs.append({
                        "success": True,
                        "code": response.text,
                        "model": model_name,
                    })
                else:
                    reason = response.candidates[0].finish_reason if response.candidates else "Unknown"
                    error_message = f"Model {model_name} produced an empty response. Finish Reason: {reason}"
                    print(error_message)
                    outputs.append({
                        "success": False,
                        "error": error_message,
                        "model": model_name,
                    })

            except Exception as e:
                error_message = f"Model {model_name} failed with an error: {e}"
                print(error_message)
                outputs.append({
                    "success": False,
                    "error": error_message,
                    "model": model_name,
                })
                continue
        
        return outputs

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("API")
    if not api_key:
        raise ValueError("API key not found in environment variables.")
    gemini_model = GeminiModel(api_key)
    prompts = [
        "Write a Linux device driver for a simple character device.",
        "Implement a Linux kernel module that logs messages to the kernel log.",
    ]
    results = gemini_model.generate_code(prompts)
    #save results to json
    import json
    with open("results.json", "w") as f:
        json.dump(results, f, indent=4) 

    
    