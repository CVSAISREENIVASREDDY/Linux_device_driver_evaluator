import re 
import os 
import sys 
from dotenv import load_dotenv 
load_dotenv() 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 
from llm.model import GeminiModel 
from evaluators.prompt_complexity import get_prompt_weight

model = GeminiModel(api_key=os.getenv("API")) 

class total_evaluator:
    
    def __init__(self):
        pass 
    
    def generate_code(self,prompt : str):
        """
        Generates C code using all available Gemini models for each prompt.
        Returns a list of dictionaries with the model name and generated code.
        """
        print(f"models are generating responses for prompt ") 
        return model._generate_code_per_prompt(prompt)  
      
    
    
    def evaluate_code(self, code: str):
        """
        Evaluates the generated C code using various evaluators.
        Returns a dictionary with evaluation results.
        """
        from evaluators.compilation import KernelModuleCompiler
        from evaluators.security import KernelVulnerabilityScanner
        from evaluators.code_quality import HybridCodeQualityAnalyzer
        
        compilation_evaluator = KernelModuleCompiler()
        security_evaluator = KernelVulnerabilityScanner()
        code_quality_analyzer = HybridCodeQualityAnalyzer()
        
        print("Evaluating code for compilation, security, and quality...")
        compilation_results = compilation_evaluator.evaluate_compilation(code)  

        print("evaluating security...")
        security_scores = security_evaluator.evaluate_security(code) 

        print("evaluating code quality...")
        quality_scores = code_quality_analyzer.evaluate(code) 
        
        print("Evaluation completed.") 
        return {
            "compilation": compilation_results,
            "security": security_scores,
            "code_quality": quality_scores
        }  

    def evaluate(self, prompt: str):
        """
        Evaluates a list of prompts by generating code and running all evaluations.
        Returns a dictionary with prompt weights, generated code, and evaluation results.
        """
        prompt_weight = get_prompt_weight(prompt)
        responses = self.generate_code(prompt)
        
        evaluation_results = {} 
       
        for model_name, response in responses.items():
            code = response['code'] 
            if not response['success']:
                print(f"Model {model_name} failed to generate code: {response['error']}")
                continue
            evaluation_results[model_name] = self.evaluate_code(code)

        return {
            "prompt_weights": prompt_weight,
            "generated_code": {model_name: response['code'] for model_name, response in responses.items()},
            "evaluation_results": evaluation_results
        } 
    
if __name__ == "__main__": 
    
    evaluator = total_evaluator() 

    sample_prompts = [
        "Write a Linux kernel driver for a simple device.",
        "Implement a character device driver with basic read/write operations.",
        "Create a kernel module that interacts with hardware."
    ]

    results = [] 
    for prompt in sample_prompts:
        print(f"Evaluating prompt: {prompt}")
        result = evaluator.evaluate(prompt)
        results.append(result) 

