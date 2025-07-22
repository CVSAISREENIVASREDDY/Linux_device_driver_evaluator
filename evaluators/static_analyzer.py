import re
from typing import Dict

class AdvancedStaticAnalyzer:
    def __init__(self):
        """Initializes the analyzer."""
        self.metrics = {}
        self.dependency_graph = {}

    def deep_static_analysis(self, code: str) -> Dict:
        """Comprehensive static analysis using multiple techniques."""
        
        results = {
            # 'syntax_analysis': self._analyze_syntax_patterns(code),
            'semantic_analysis': self._analyze_semantic_patterns(code),
            'control_flow_analysis': self._analyze_control_flow(code),
            'data_flow_analysis': self._analyze_data_flow(code),
            'dependency_analysis': self._analyze_dependencies(code),
            'complexity_metrics': self._calculate_complexity_metrics(code),
            'kernel_score': self._analyze_kernel_patterns(code),
            'functionality': self.evaluate_functionality(code)
        }
        
        return results

    def evaluate_functionality(self, code: str) -> Dict[str, float]:
        """
        Evaluates the driver's functionality based on implemented operations,
        error handling, and edge case considerations.
        """
        essential_ops = [".open", ".release", ".read", ".write"]
        ops_found = sum(1 for op in essential_ops if op in code)
        total_ops = len(essential_ops)
        if "struct file_operations" in code:
            ops_found += 1
            total_ops += 1
        basic_operations_score = ops_found / total_ops if total_ops > 0 else 0.0

        total_returns = len(re.findall(r'\breturn\b', code))
        error_code_returns = len(re.findall(r'\breturn\s+-E[A-Z]+', code))
        error_return_ratio = error_code_returns / total_returns if total_returns > 0 else 0.0

        fallible_calls = list(re.finditer(r'(\w+)\s*=\s*(kmalloc|kzalloc|copy_from_user)\s*\(', code))
        checks_found = 0
        for call in fallible_calls:
            var_name = call.group(1)
            search_region = code[call.end():call.end() + 200]
            if re.search(r'if\s*\(([^)]*!%s|%s\s*==\s*NULL)' % (re.escape(var_name), re.escape(var_name)), search_region):
                checks_found += 1
        
        fallible_check_ratio = checks_found / len(fallible_calls) if fallible_calls else 1.0
        

        error_handling_score = (fallible_check_ratio * 0.4) + (error_return_ratio * 0.6)

 
        edge_case_score = 0.0
        
        if re.search(r'if\s*\([^)]*NULL', code) or re.search(r'if\s*\(\s*!\s*\w+', code):
            edge_case_score += 0.3
        
        if re.search(r'if\s*\([^)]*(len|size|count)', code):
            edge_case_score += 0.3
            
        unique_error_codes = set(re.findall(r'return\s+(-E[A-Z]+)', code))
        if len(unique_error_codes) > 2:
            edge_case_score += 0.2

        return {
            "basic_operations": round(basic_operations_score, 2),
            "error_handling": round(error_handling_score, 2),
            "edge_cases": round(min(1.0, edge_case_score), 2)
        }


    def _analyze_syntax_patterns(self, code: str) -> Dict:
        """deep syntax pattern analysis"""
        patterns = {
            'function_definitions': [],
            'variable_declarations': [],
            'struct_definitions': [],
            'macro_usage': [],
            'include_dependencies': []
        }
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            func_match = re.search(r'^\s*(?:static\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*{?', line)
            if func_match and not re.search(r'(if|while|for)', line):
                patterns['function_definitions'].append({
                    'name': func_match.group(1),
                    'line': i,
                    'signature': line.strip()
                })
            
            var_match = re.search(r'^\s*(?:static\s+)?(?:const\s+)?(\w+)\s+(\w+)', line)
            if var_match and not re.search(r'(return|if|while)', line):
                patterns['variable_declarations'].append({
                    'type': var_match.group(1),
                    'name': var_match.group(2),
                    'line': i
                })
        
        return patterns
    
    def _analyze_semantic_patterns(self, code: str) -> Dict:
        """semantic analysis for meaning and intent"""
        semantic_issues = []
        
        function_calls = re.findall(r'(\w+)\s*\([^)]*\)', code)
        call_frequency = {}
        for call in function_calls:
            call_frequency[call] = call_frequency.get(call, 0) + 1
        
        if 'kmalloc' in call_frequency and call_frequency.get('kfree', 0) == 0:
            semantic_issues.append({
                'type': 'memory_leak_pattern',
                'severity': 'high',
                'description': 'kmalloc called without corresponding kfree'
            })
        
        error_returns = len(re.findall(r'return\s+-E[A-Z]+', code))
        total_returns = len(re.findall(r'return\s+', code))
        
        error_handling_ratio = error_returns / max(1, total_returns)
        
        return {
            'function_call_frequency': call_frequency,
            'semantic_issues': semantic_issues,
            'error_handling_ratio': error_handling_ratio,
        }
    
    def _analyze_control_flow(self, code: str) -> Dict:
        """control flow analysis for complexity and paths"""
        
        control_structures = {
            'if_statements': len(re.findall(r'\bif\s*\(', code)),
            'for_loops': len(re.findall(r'\bfor\s*\(', code)),
            'while_loops': len(re.findall(r'\bwhile\s*\(', code)),
            'switch_statements': len(re.findall(r'\bswitch\s*\(', code)),
            'goto_statements': len(re.findall(r'\bgoto\s+\w+', code))
        }
        
        complexity = 1 + sum(control_structures.values()) - control_structures['goto_statements']
        max_nesting = self._calculate_max_nesting_depth(code)
        
        return {
            'control_structures': control_structures,
            'cyclomatic_complexity': complexity,
            'max_nesting_depth': max_nesting,
        }
    
    def _analyze_data_flow(self, code: str) -> Dict:
        """data flow analysis for variable usage patterns"""
        variable_definitions = {}
        variable_usages = {}
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            var_def = re.search(r'(\w+)\s*=\s*', line)
            if var_def:
                var_name = var_def.group(1)
                if var_name not in variable_definitions:
                    variable_definitions[var_name] = []
                variable_definitions[var_name].append(i)
            
            for var in variable_definitions:
                if var in line and f'{var}=' not in line:
                    if var not in variable_usages:
                        variable_usages[var] = []
                    variable_usages[var].append(i)
        
        unused_variables = [var for var in variable_definitions if var not in variable_usages]
        
        return {
            'variable_definitions': variable_definitions,
            'variable_usages': variable_usages,
            'unused_variables': unused_variables,
        }
    
    def _analyze_dependencies(self, code: str) -> Dict:
        """analyze code dependencies and coupling"""
        includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', code)
        kernel_includes = [inc for inc in includes if inc.startswith('linux/')]
        system_includes = [inc for inc in includes if not inc.startswith('linux/')]
        function_calls = re.findall(r'(\w+)\s*\(', code)
        external_calls = [call for call in function_calls if call in ['kmalloc', 'printk', 'copy_from_user']]
        
        return {
            'total_includes': len(includes),
            'kernel_includes': kernel_includes,
            'system_includes': system_includes,
            'external_function_calls': external_calls,
        }
    
    def _calculate_complexity_metrics(self, code: str) -> Dict:
        """calculate various complexity metrics"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        i = comment_chars = 0
        while i < len(code):
            if code[i:i+2] == '//': i+=2; j=code.find('\n',i); comment_chars+=j-i if j!=-1 else len(code)-i; i=j if j!=-1 else len(code)
            elif code[i:i+2] == '/*': i+=2; j=code.find('*/',i); comment_chars+=j-i if j!=-1 else 0; i=j+2 if j!=-1 else len(code)
            else: i += 1  

        metrics = {
            'lines_of_code': len(non_empty_lines),
            'function_count': len(re.findall(r'^\s*(?:static\s+)?\w+\s+\w+\s*\([^)]*\)\s*{', code, re.MULTILINE)),
            'average_function_length': 0,
            'comment_ratio': 0
        }

        if metrics['function_count'] > 0:
            metrics['average_function_length'] = metrics['lines_of_code'] / metrics['function_count']
        
        if len(lines) > 0:
            metrics['comment_ratio'] = comment_chars / len(''.join(lines))
        
        return metrics
    
    def _analyze_kernel_patterns(self, code: str) -> Dict:
        """kernel-specific pattern analysis"""
        kernel_patterns = {
            'module_structure': {
                'has_init': 'module_init' in code,
                'has_exit': 'module_exit' in code,
                'has_license': 'MODULE_LICENSE' in code,
                'has_author': 'MODULE_AUTHOR' in code
            },
            'device_driver_patterns': {
                'file_operations': 'file_operations' in code,
                'device_open': 'device_open' in code or '.open' in code,
                'device_release': 'device_release' in code or '.release' in code,
                'device_read': 'device_read' in code or '.read' in code,
                'device_write': 'device_write' in code or '.write' in code
            },
            'memory_patterns': {
                'uses_kmalloc': 'kmalloc' in code,
                'uses_kfree': 'kfree' in code,
                'uses_copy_from_user': 'copy_from_user' in code,
                'uses_copy_to_user': 'copy_to_user' in code
            }
        }
        
        module_score = sum(kernel_patterns['module_structure'].values()) / len(kernel_patterns['module_structure']) * 100
        driver_score = sum(kernel_patterns['device_driver_patterns'].values()) / len(kernel_patterns['device_driver_patterns']) * 100
        memory_score = sum(kernel_patterns['memory_patterns'].values()) / len(kernel_patterns['memory_patterns']) * 100
        
        overall_kernel_score = (module_score + driver_score + memory_score) / 3
        return overall_kernel_score
    
    def _calculate_max_nesting_depth(self, code: str) -> int:
        """calculate maximum nesting depth"""
        max_depth = 0
        current_depth = 0
        
        for char in code:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth


if __name__ == '__main__':
    sample_driver_code = """
    #include <linux/module.h>
    #include <linux/fs.h>
    #include <linux/uaccess.h>
    #include <linux/slab.h>

    static int my_open(struct inode *inode, struct file *file) { return 0; }
    static int my_release(struct inode *inode, struct file *file) { return 0; }

    static ssize_t my_read(struct file *file, char __user *buf, size_t len, loff_t *off) {
        if (len > 1024) {
            return -EINVAL; // Handle edge case: oversized read
        } //alsdfqweiuf
        return 0; 
    }

    static ssize_t my_write(struct file *file, const char __user *buf, size_t len, loff_t *off) {
        char *kbuf;
        if (!buf) {
            return -EFAULT; // Handle edge case: NULL buffer
        }
        kbuf = kmalloc(len, GFP_KERNEL);
        if (!kbuf) {
            return -ENOMEM; 
        // Handle error: kmalloc failure
        }
        kfree(kbuf);
        return len;
    }

    static const struct file_operations my_fops = {
        .owner = THIS_MODULE,
        .open = my_open,
        .release = my_release,
        .read = my_read,
        .write = my_write,
    };
    """
    analyzer = AdvancedStaticAnalyzer()
    
    static_analysis_report = analyzer.deep_static_analysis(sample_driver_code)

    print("Static Analysis Report:", static_analysis_report)
   
    with open("static_analysis_report.json", "w") as f:
        import json
        json.dump(static_analysis_report, f, indent=4) 

