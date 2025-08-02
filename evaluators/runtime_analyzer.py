import os
import tempfile
import subprocess
import re
import shutil
from typing import Dict
import time
import uuid
import psutil  

class RuntimeProfiler:
    def __init__(self):
        self.kernel_dir = tempfile.mkdtemp()
        self.module_name = "test_driver"
        self.module_file = os.path.join(self.kernel_dir, f"{self.module_name}.c")
        self.unique_id = str(uuid.uuid4())

    def _write_driver_and_makefile(self, driver_code: str) -> None:
        driver_code_with_id = driver_code.replace(
            'printk(KERN_INFO "', f'printk(KERN_INFO "[{self.unique_id}] '
        )
        with open(self.module_file, 'w') as f:
            f.write(driver_code_with_id)

        makefile_path = os.path.join(self.kernel_dir, "Makefile")
        with open(makefile_path, 'w') as f:
            f.write(f"""
obj-m += {self.module_name}.o

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

all:
\tmake -C $(KDIR) M=$(PWD) modules

clean:
\tmake -C $(KDIR) M=$(PWD) clean
""")

    def _build_module(self) -> bool:
        try:
            result = subprocess.run(
                ['make'],
                cwd=self.kernel_dir,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print("Build failed.")
            print("Stdout:", e.stdout)
            print("Stderr:", e.stderr)
            return False
        except Exception as e:
            print(f"An unexpected error occurred during build: {e}")
            return False

    def _insert_module(self) -> bool:
        try:
            subprocess.run(
                ['sudo', 'insmod', f'./{self.module_name}.ko'],
                cwd=self.kernel_dir,
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print("Insert failed.")
            print("Stderr:", e.stderr)
            return False

    def _remove_module(self):
        try:
            subprocess.run(['sudo', 'rmmod', self.module_name], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if "Module does not exist" in e.stderr:
                print("Module was not loaded or already removed.")
            else:
                print("Remove failed:", e.stderr)
        except Exception as e:
            print("An unexpected error occurred during module removal:", str(e))

    def _read_dmesg(self) -> str:
        try:
            result = subprocess.run(['dmesg'], capture_output=True, text=True, check=True)
            return result.stdout
        except Exception as e:
            return f"Error reading dmesg: {e}"

    def _get_module_metrics(self) -> Dict:
        metrics = {}
        try:
            with open('/proc/modules', 'r') as f:
                for line in f:
                    if self.module_name in line:
                        parts = line.split()
                        metrics['size'] = int(parts[1])
                        metrics['ref_count'] = int(parts[2])
                        break
        except Exception as e:
            metrics['error'] = f"Module read error: {e}"
        return metrics

    def analyze_driver(self, driver_code: str) -> Dict:
        self._write_driver_and_makefile(driver_code)
        metrics = {'build_success': False, 'inserted': False}

        try:
            if not self._build_module():
                metrics['error'] = "Build failed"
                return metrics
            metrics['build_success'] = True

            start_time = time.time()
            if not self._insert_module():
                metrics['error'] = "Insert failed"
                return metrics
            metrics['inserted'] = True
            end_time = time.time()

            time.sleep(1)

            dmesg_after = self._read_dmesg()
            dmesg_diff = [line for line in dmesg_after.splitlines() if self.unique_id in line]

            metrics.update(self._get_module_metrics())
            metrics['execution_time_sec'] = round(end_time - start_time, 6)
            metrics['dmesg_output'] = dmesg_diff

        finally:
            self._remove_module()
            shutil.rmtree(self.kernel_dir)

        return metrics


if __name__ == "__main__":
    dummy_driver_code = """
#include <linux/module.h>
#include <linux/init.h>
#include <linux/kernel.h>

static int __init my_init(void) {
    printk(KERN_INFO "Dummy driver loaded\\n");
    return 0;
}

static void __exit my_exit(void) {
    printk(KERN_INFO "Dummy driver removed\\n");
}

module_init(my_init);
module_exit(my_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Google");
MODULE_DESCRIPTION("A dummy test module");
"""
    profiler = RuntimeProfiler()

    proc = psutil.Process(os.getpid())
    cpu_start = proc.cpu_times()
    mem_start = proc.memory_info().rss

    result = profiler.analyze_driver(dummy_driver_code)

    cpu_end = proc.cpu_times()
    mem_end = proc.memory_info().rss

    result["cpu_usage"] = {
        "user_time_sec": round(cpu_end.user - cpu_start.user, 6),
        "system_time_sec": round(cpu_end.system - cpu_start.system, 6)
    }
    result["peak_memory_kb"] = mem_end // 1024  
    
    with open("runtime_report.json", "w") as f:
        import json
        json.dump(result, f, indent=4) 