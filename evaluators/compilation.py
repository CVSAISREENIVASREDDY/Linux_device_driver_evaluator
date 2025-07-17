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
        # A standard Makefile for building a single-file kernel module.
        makefile_content = """ 
        obj-m += driver_under_test.o
        KDIR := /lib/modules/$(shell uname -r)/build
        PWD := $(shell pwd)

        default:
            $(MAKE) -C $(KDIR) M=$(PWD) modules

        clean:
	        $(MAKE) -C $(KDIR) M=$(PWD) clean
        """
        
        # Using a temporary directory ensures a clean build environment.
        with tempfile.TemporaryDirectory() as temp_dir:
            driver_file = os.path.join(temp_dir, 'driver_under_test.c')
            makefile = os.path.join(temp_dir, 'Makefile')
            
            with open(driver_file, 'w') as f:
                f.write(code)
            with open(makefile, 'w') as f:
                f.write(makefile_content)
            
            try:
                # Execute the build command from within the temporary directory.
                result = subprocess.run(
                    ['make'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                build_output = result.stdout + result.stderr
                
                # --- New Parsing Logic ---
                # Use regex to count all instances of "error:" and "warning:".
                errors_count = len(re.findall(r':\berror:', build_output))
                warnings_count = len(re.findall(r':\bwarning:', build_output))
                
                # The success_rate is 1.0 if compilation succeeds (exit code 0),
                # and 0.0 otherwise. This could be made more nuanced by applying
                # a penalty for warnings, e.g., `1.0 - (warnings_count * 0.01)`.
                success_rate = 1.0 if result.returncode == 0 else 0.0
                
                # Return the structured dictionary.
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
                    "errors_count": 1, # The timeout is considered a build error
                    "raw_output": "Build process timed out." # Optional: add raw output for context
                }
            except Exception as e:
                return {
                    "success_rate": 0.0,
                    "warnings_count": 0,
                    "errors_count": 1,
                    "raw_output": f"An unexpected error occurred: {e}"
                }

if __name__ == '__main__':
    # Sample kernel code with a warning (unused variable) and an error (missing semicolon)
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
    
    print("Compilation Metrics:")       
    print(compilation_metrics)          