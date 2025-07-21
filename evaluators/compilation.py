import subprocess
import tempfile
import os
import re
from typing import Dict

class KernelModuleCompiler:
    """
    Compiles kernel module code in a temporary environment and evaluates
    the results to produce structured compilation metrics.
    """
    def __init__(self):
        self.compilation_results = {}

    def evaluate_compilation(self, code: str) -> Dict:
        """
        Compiles the driver code and parses the compiler output to generate metrics.
        """
        
        makefile_content = """ 
        obj-m += driver_under_test.o
        KDIR := /lib/modules/$(shell uname -r)/build
        PWD := $(shell pwd)

        default:
            $(MAKE) -C $(KDIR) M=$(PWD) modules

        clean:
	        $(MAKE) -C $(KDIR) M=$(PWD) clean
        """
        
        with tempfile.TemporaryDirectory() as temp_dir:
            driver_file = os.path.join(temp_dir, 'driver_under_test.c')
            makefile = os.path.join(temp_dir, 'Makefile')
            
            with open(driver_file, 'w') as f:
                f.write(code)
            with open(makefile, 'w') as f:
                f.write(makefile_content)
            
            try:
                result = subprocess.run(
                    ['make'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                build_output = result.stdout + result.stderr
                
                errors_count = len(re.findall(r':\berror:', build_output))
                warnings_count = len(re.findall(r':\bwarning:', build_output))
                
                success_rate = 1.0 if result.returncode == 0 else 0.0
                
                return {
                    "success_rate": success_rate,
                    "warnings_count": warnings_count,
                    "errors_count": errors_count,
                    "raw_output": build_output.strip() 
                } 
            except subprocess.TimeoutExpired:
                return {
                    "success_rate": 0.0,
                    "warnings_count": 0,
                    "errors_count": 1, 
                    "raw_output": "Build process timed out." 
                }
            except Exception as e:
                return {
                    "success_rate": 0.0,
                    "warnings_count": 0,
                    "errors_count": 1,
                    "raw_output": f"An unexpected error occurred: {e}"
                }

if __name__ == '__main__':
    
    sample_code_with_issues = """
    #include <linux/module.h>
    #include <linux/init.h>

    static int __init my_init(void) {
        int unused_var = 5; // This will cause a warning.
        printk(KERN_INFO "Hello, world\\n") // This will cause an error.
        return 0;
    }

    static void __exit my_exit(void) {
        printk(KERN_INFO "Goodbye, world\\n");
    }

    module_init(my_init);
    module_exit(my_exit);
    MODULE_LICENSE("GPL");
    """
    
    compiler = KernelModuleCompiler()
    compilation_metrics = compiler.evaluate_compilation(sample_code_with_issues)
    
    import json 
    with open("compilation_metrics.json", "w") as f:
        json.dump(compilation_metrics, f, indent=4)
    print("Compilation Metrics:")       
    print(compilation_metrics)          