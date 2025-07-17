import re 

def get_prompt_weight(prompt: str):
        
        complexity_indicators = {
            'technical_terms': len(re.findall(r'\b(driver|kernel|module|device|interrupt|DMA|mutex|spinlock)\b', prompt.lower())),
            'specific_requirements': len(re.findall(r'\b(must|should|implement|support|handle)\b', prompt.lower())),
            'constraints': len(re.findall(r'\b(without|avoid|prevent|ensure|guarantee)\b', prompt.lower())),
            'word_count': len(prompt.split())
        }
        
        complexity_score = min(100, (
            complexity_indicators['technical_terms'] * 20 +
            complexity_indicators['specific_requirements'] * 12 +
            complexity_indicators['constraints'] * 15 +
            complexity_indicators['word_count'] * 0.8
        ))
        
        return complexity_score * 0.01 