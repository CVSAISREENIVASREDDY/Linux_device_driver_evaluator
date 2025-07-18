import re 
import os 
import sys 
from dotenv import load_dotenv 
load_dotenv() 
import json

from evaluators.prompt_complexity import get_prompt_weight

class total_evaluator:
    
    def __init__(self):
        pass 

    def evaluate_code(self, code: str):
        """
        Evaluates the generated C code using various evaluators.
        Returns a dictionary with evaluation results.
        """
        from evaluators.compilation import KernelModuleCompiler
        from evaluators.security import KernelVulnerabilityScanner
        from evaluators.code_quality import HybridCodeQualityAnalyzer
        from evaluators.static_analyzer import AdvancedStaticAnalyzer 

        static_analyzer = AdvancedStaticAnalyzer() 
        compilation_evaluator = KernelModuleCompiler()
        security_evaluator = KernelVulnerabilityScanner()
        code_quality_analyzer = HybridCodeQualityAnalyzer()
        
    
        evaluated_results = {
            'static_analysis_results' : static_analyzer.deep_static_analysis(code),
            'compilation_results' : compilation_evaluator.evaluate_compilation(code),
            'security_results' : security_evaluator.evaluate_security(code),
            'code_quality_results' : code_quality_analyzer.evaluate(code)
        } 

        return evaluated_results

    def evaluate(self, responses: dict):
        """
        Evaluates a list of prompts by generating code and running all evaluations.
        Returns a dictionary with prompt weights, generated code, and evaluation results.
        """ 
        evaluation_results = {}
        for prompt in responses.keys():

            evaluation_results[prompt] = {}
            prompt_weight = get_prompt_weight(prompt)
            evaluation_results[prompt]['prompt_weight'] = prompt_weight

            for model_name, response in responses[prompt].items():
                evaluation_results[prompt]["Model Name"] = model_name
                
                code = response['code'] 
                if not response['success']:
                    print(f"Model {model_name} failed to generate code: {response['code']}")
                    continue 
                
                evaluation_results[prompt][f'{model_name} result'] = self.evaluate_code(code)

        return evaluation_results
    def get_response(self):
        responses = json.load(open("all_prompt_responses.json", "r")) 
        return responses 
    
if __name__ == "__main__": 
    
    evaluator = total_evaluator() 

    sample_prompts = [
        "Write a Linux kernel driver for a simple device.",
        "2Implement a character device driver with basic read/write operations.",
        "Create a kernel module that interacts with hardware."
    ]

    all_prompt_responses = evaluator.get_response()
    
    evaluation_results = evaluator.evaluate(all_prompt_responses) 

    with open("evaluation_results.json", "w") as f:
        json.dump(evaluation_results, f, indent=4)
    