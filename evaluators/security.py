import re
from typing import Dict, List

class KernelVulnerabilityScanner:
    def __init__(self):
        """
        Initializes the scanner with vulnerability patterns specific to Linux kernel drivers.
        """
        self.vulnerability_patterns = {
            'unchecked_user_copy': {
                'patterns': [r'copy_from_user\s*\(', r'copy_to_user\s*\('],
                'severity': 'critical',
                'recommendation': 'Always check the return value of copy_from_user/copy_to_user.'
            },
            'unchecked_kernel_alloc': {
                'patterns': [r'kmalloc\s*\(', r'kzalloc\s*\('],
                'severity': 'high',
                'recommendation': 'Always check the result of kmalloc/kzalloc for NULL to prevent kernel panic.'
            },
            'kernel_format_string': {
                'patterns': [r'printk\s*\([^,]+\);'],
                'severity': 'high',
                'recommendation': 'Avoid passing raw buffers to printk; use a format specifier like "%s".'
            },
            'integer_overflow': {
                'patterns': [r'\w+\s*\+\s*\w+\s*>', r'size\s*\*\s*count'],
                'severity': 'medium',
                'recommendation': 'Check for integer overflows before allocating memory.'
            },
            
            'direct_jiffies_access': {
                'patterns': [r'\Wjiffies\W'],
                'severity': 'medium',
                'recommendation': 'Use get_jiffies_64() to safely read the jiffies counter.'
            },

            'unsafe_string_function': {
                'patterns': [r'\Wstrcpy\s*\(', r'\Wsprintf\s*\('],
                'severity': 'critical',
                'recommendation': 'Replace strcpy/sprintf with safer kernel APIs like strscpy/scnprintf.'
            }
        }

    def _find_vulnerabilities(self, code: str) -> List[Dict]:
        """A private method to find all vulnerabilities based on defined patterns."""
        found_vulnerabilities = []
        for vuln_type, vuln_data in self.vulnerability_patterns.items():
            for pattern in vuln_data['patterns']:
                try:
                    if re.search(pattern, code):
                        found_vulnerabilities.append({
                            'type': vuln_type,
                            'severity': vuln_data['severity']
                        })
                except re.error as e:
                    print(f"Regex error in pattern {pattern}: {e}")
        return found_vulnerabilities

    def evaluate_security(self, code: str) -> Dict[str, float]:
        """
        Scans kernel driver code and returns security scores for relevant categories.
        """
        vulnerabilities = self._find_vulnerabilities(code)

        scores = {
            "kernel_memory_safety": 1.0,
            "kernel_concurrency": 1.0,
            "kernel_api_misuse": 1.0
        }

        category_map = {
            'unchecked_user_copy': 'kernel_memory_safety',
            'unchecked_kernel_alloc': 'kernel_memory_safety',
            'kernel_format_string': 'kernel_memory_safety',
            'integer_overflow': 'kernel_memory_safety',
            'direct_jiffies_access': 'kernel_concurrency',
            'unsafe_string_function': 'kernel_api_misuse'
        }
        
        penalty_weights = {
            'critical': 0.40,
            'high': 0.25,
            'medium': 0.15,
            'low': 0.05
        }

        for vuln in vulnerabilities:
            category = category_map.get(vuln['type'])
            if category in scores:
                penalty = penalty_weights.get(vuln['severity'], 0.05)
                scores[category] -= penalty
        
        for category, score in scores.items():
            scores[category] = round(max(0.0, score), 2)
            
        return scores


if __name__ == '__main__':
    sample_kernel_code = """
    #include <linux/module.h>
    #include <linux/slab.h>
    #include <linux/uaccess.h>
    #include <linux/jiffies.h>

    static ssize_t my_write(struct file *f, const char __user *buf, size_t len, loff_t *off) {
        char *kbuf;
        unsigned long current_time;

        // HIGH: Missing NULL check after kmalloc
        kbuf = kmalloc(len, GFP_KERNEL);

        // CRITICAL: Missing return value check for copy_from_user
        copy_from_user(kbuf, buf, len);

        // CRITICAL: Unsafe string function in kernel
        char temp[10];
        strcpy(temp, kbuf); 

        // HIGH: Potential format string bug if kbuf is user-controlled
        printk(kbuf); 
        
        // MEDIUM: Direct access to jiffies can be problematic
        current_time = jiffies;

        kfree(kbuf);
        return len;
    }
    """
    
    scanner = KernelVulnerabilityScanner()
    security_metrics = scanner.evaluate_security(sample_kernel_code)

    print("Kernel Driver Security Evaluation:")
    print(security_metrics)

    import json
    with open("security_report.json", "w") as f:
        json.dump(security_metrics, f, indent=4)
