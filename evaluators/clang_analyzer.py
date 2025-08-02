import subprocess
import json
import re
import tempfile
import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ClangIssue:
    severity: str
    type: str
    line: int
    column: int
    message: str
    category: str
    file_path: str
    suggestion: str = ""

class EnhancedClangAnalyzer:
    """
    Clang-Tidy analyzer modified to be configurable and run on Windows.
    """
    def __init__(self, clang_executable_path: str, include_paths: List[str] = None):

        self.clang_executable_path = clang_executable_path
        self.clang_available = self._check_clang_availability()
        self.kernel_header_paths = include_paths if include_paths is not None else []
        self.kernel_checks = [
            'bugprone-unused-parameter', 'bugprone-unused-variable',
            'misc-unused-parameters', 'misc-unused-variables',
            'readability-braces-around-statements', 'readability-misleading-indentation',
            'performance-unnecessary-copy-initialization',
            'clang-analyzer-core.NullDereference', 'clang-analyzer-deadcode.DeadStores'
        ]

    def _check_clang_availability(self) -> bool:
        """Checks if the configured clang-tidy executable is available."""
        if not os.path.exists(self.clang_executable_path):
            print(f"Warning: Clang-Tidy executable not found at '{self.clang_executable_path}'")
            return False
        try:
            # Use the full path to the executable for the version check.
            result = subprocess.run([self.clang_executable_path, '--version'], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"Clang-Tidy at '{self.clang_executable_path}' is not runnable. Error: {e}")
            return False

    def analyze_code_detailed(self, code: str) -> Dict:
        """Analyzes a string of C code using clang-tidy."""
        if not self.clang_available: 
            return {"error": "clang-tidy not available or configured incorrectly", "fallback": True}
        
        # Use a temporary file with a .c extension so clang-tidy recognizes it as C code.
        # delete=False is necessary to pass the path to another process on Windows.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False, dir='.') as temp_file:
            temp_filepath = temp_file.name
            temp_file.write(code)
        
        try:
            return self._run_detailed_analysis(temp_filepath)
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def _run_detailed_analysis(self, filepath: str) -> Dict:
        """Constructs and runs the clang-tidy command."""
        checks = ','.join(self.kernel_checks)
        # Generate include flags from the user-provided list of paths.
        include_flags = [f'-I{path}' for path in self.kernel_header_paths]
        
        # Kernel-specific defines from your original code.
        defines = ['-D__KERNEL__', '-DMODULE', '-DREAD_ONCE(x)=(x)', '-DWRITE_ONCE(x,v)=((x)=(v))', '-D__user=', '-D__iomem=', '-D__must_check=']
        
        # The command now uses the full executable path and configured includes.
        cmd = [self.clang_executable_path, filepath, f'--checks={checks}', '--header-filter=.*', '--', *include_flags, *defines, '-std=gnu89']
        
        try:
            # We increase the timeout slightly as analysis can sometimes be slow.
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # Combine stdout and stderr as clang-tidy writes to both.
            output = result.stdout + result.stderr
            issues = self._parse_and_filter_output(output, os.path.basename(filepath))
            return {"clang_available": True, "issues": [issue.__dict__ for issue in issues]}
        except Exception as e:
            print(f"Clang-Tidy analysis failed: {str(e)}")
            return {"error": f"clang analysis failed: {str(e)}"}

    def _parse_and_filter_output(self, output: str, temp_filename: str) -> List[ClangIssue]:
        """Parses the clang-tidy output string. The logic remains the same."""
        issues = []
        # Regex to find issues, which works perfectly on Windows output.
        pattern = r'([^:]+):(\d+):(\d+):\s+(warning|error|note):\s+(.+?)\s+\[([^\]]+)\]'
        for match in re.finditer(pattern, output):
            file_path, line_num, col, severity, message, check_name = match.groups()
            
            # Filter out issues from header files, only show issues in our temp source file.
            if os.path.basename(file_path) != temp_filename:
                continue

            category = self._categorize_detailed_issue(check_name)
            issues.append(ClangIssue(severity=severity, type=check_name, line=int(line_num), column=int(col), message=message.strip(), category=category, file_path=file_path))
        return issues

    def _categorize_detailed_issue(self, check_name: str) -> str:
        """Categorization logic remains the same."""
        check_lower = check_name.lower()
        if 'security' in check_lower or 'null' in check_lower: return 'security'
        if 'readability' in check_lower: return 'style'
        if 'bugprone' in check_lower or 'unused' in check_lower or 'deadcode' in check_lower: return 'maintainability'
        if 'performance' in check_lower: return 'performance'
        return 'general'

class HybridCodeQualityAnalyzer:
    """
    This class remains mostly the same, but now it must be initialized with the
    path to clang-tidy and the necessary include directories.
    """
    def __init__(self):
        """Initializes the analyzer, combining Clang-Tidy with regex methods."""
        clang_executable_path = r'C:\Program Files\LLVM\bin\clang-tidy.exe'
        include_paths = [r'C:\msys64\mingw64\include']
        self.clang_analyzer = EnhancedClangAnalyzer(clang_executable_path, include_paths)

    def _calculate_documentation_score(self, code: str) -> float:
        """This regex-based method is platform-independent and remains unchanged."""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        if not non_empty_lines:
            return 0.0

        comment_lines = sum(1 for line in non_empty_lines if line.strip().startswith(('//', '/*', '*/', '*')))
        comment_ratio = comment_lines / len(non_empty_lines)
        comment_ratio_score = min(1.0, comment_ratio / 0.2) 

        functions = list(re.finditer(r'^\s*(?:static\s+)?\w+\s+\w+\s*\([^)]*\)\s*{', code, re.MULTILINE))
        documented_functions = 0
        if functions:
            code_lines = code.split('\n')
            for func in functions:
                func_line_num = code.count('\n', 0, func.start())
                if func_line_num > 0 and code_lines[func_line_num - 1].strip().startswith(('*/', '//', '/*')):
                    documented_functions += 1
            function_doc_score = documented_functions / len(functions)
        else:
            function_doc_score = 1.0

        return (comment_ratio_score * 0.5) + (function_doc_score * 0.5)

    def evaluate(self, code: str) -> Dict[str, float]:
        """The evaluation logic remains identical."""
        clang_results = self.clang_analyzer.analyze_code_detailed(code)

        style_score = 1.0
        maintainability_score = 1.0

        if "issues" in clang_results and clang_results["issues"]:
            issues = clang_results["issues"]
            style_penalty = 0.0
            maintainability_penalty = 0.0

            for issue in issues:
                category = issue.get('category')
                penalty_amount = 0.15 if issue.get('severity') == 'error' else 0.05

                if category == 'style':
                    style_penalty += penalty_amount
                elif category in ['maintainability', 'performance', 'security']:
                    maintainability_penalty += penalty_amount
            
            style_score = max(0.0, 1.0 - style_penalty)
            maintainability_score = max(0.0, 1.0 - maintainability_penalty)

        documentation_score = self._calculate_documentation_score(code)

        return {
            "style_compliance": round(style_score, 2),
            "documentation": round(documentation_score, 2),
            "maintainability": round(maintainability_score, 2)
        }

if __name__ == '__main__':

    sample_driver_code = """
    #include <stdio.h>

    // A function with a comment
    int documented_function(int p) { 
        if(p > 10) 
             return 1;
        return 0;
    }

    /* Missing function comment here */
    int undocumented_function() {
        int x = 5; 
        return 0;
    }
    
    void main() {
        documented_function(11);
        undocumented_function();
    }
    """

    quality_analyzer = HybridCodeQualityAnalyzer()
    
    quality_report = quality_analyzer.evaluate(sample_driver_code)

    with open("clang_analysis_report.json", "w") as f:
        json.dump(quality_report, f, indent=4)
    
    print("\nReport saved to clang_analysis_report.json")  