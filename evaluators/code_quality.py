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
    def __init__(self, custom_header_path: str = None):
        self.clang_available = self._check_clang_availability()
        self.kernel_header_paths = self._get_all_kernel_header_paths(custom_header_path)
        self.kernel_checks = [
            'bugprone-unused-parameter', 'bugprone-unused-variable',
            'misc-unused-parameters', 'misc-unused-variables',
            'readability-braces-around-statements', 'readability-misleading-indentation',
            'performance-unnecessary-copy-initialization',
            'clang-analyzer-core.NullDereference', 'clang-analyzer-deadcode.DeadStores'
        ]

    def _check_clang_availability(self) -> bool:
        try:
            return subprocess.run(['clang-tidy', '--version'], capture_output=True, text=True, timeout=5).returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_all_kernel_header_paths(self, custom_base_path: str = None) -> List[str]:
        base_path = custom_base_path
        if not base_path:
            try:
                kernel_version = subprocess.check_output(['uname', '-r']).strip().decode()
                base_path = f"/usr/src/linux-headers-{kernel_version}"
            except:
                return ["/usr/include"]
        if not os.path.isdir(base_path):
            return ["/usr/include"]
        potential_paths = [f"{base_path}/include", f"{base_path}/arch/x86/include", "/usr/include"]
        return [path for path in potential_paths if os.path.isdir(path)]

    def analyze_code_detailed(self, code: str) -> Dict:
        if not self.clang_available:
            return {"error": "clang-tidy not available", "fallback": True}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False, dir='.') as temp_file:
            temp_filepath = temp_file.name
            temp_file.write(code)
        try:
            return self._run_detailed_analysis(temp_filepath)
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def _run_detailed_analysis(self, filepath: str) -> Dict:
        checks = ','.join(self.kernel_checks)
        include_flags = [f'-I{path}' for path in self.kernel_header_paths]
        defines = ['-D__KERNEL__', '-DMODULE', '-DREAD_ONCE(x)=(x)', '-DWRITE_ONCE(x,v)=((x)=(v))', '-D__user=', '-D__iomem=', '-D__must_check=']
        cmd = ['clang-tidy', filepath, f'--checks={checks}', '--header-filter=^$', '--', *include_flags, *defines, '-std=gnu89']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            issues = self._parse_and_filter_output(result.stdout + result.stderr)
            return {"clang_available": True, "issues": [issue.__dict__ for issue in issues]}
        except Exception as e:
            return {"error": f"clang analysis failed: {str(e)}"}

    def _parse_and_filter_output(self, output: str) -> List[ClangIssue]:
        issues = []
        pattern = r'([^:]+):(\d+):(\d+):\s+(warning|error|note):\s+(.+?)\s+\[([^\]]+)\]'
        for match in re.finditer(pattern, output):
            file_path, line_num, col, severity, message, check_name = match.groups()
            category = self._categorize_detailed_issue(check_name)
            issues.append(ClangIssue(severity=severity, type=check_name, line=int(line_num), column=int(col), message=message.strip(), category=category, file_path=file_path))
        return issues

    def _categorize_detailed_issue(self, check_name: str) -> str:
        check_lower = check_name.lower()
        if 'security' in check_lower or 'null' in check_lower: return 'security'
        if 'readability' in check_lower: return 'style'
        if 'bugprone' in check_lower or 'unused' in check_lower or 'deadcode' in check_lower: return 'maintainability'
        if 'performance' in check_lower: return 'performance'
        return 'general'

class HybridCodeQualityAnalyzer:
    def __init__(self):
        """Initializes the analyzer, combining Clang-Tidy with regex methods."""
        self.clang_analyzer = EnhancedClangAnalyzer()

    def _calculate_documentation_score(self, code: str) -> float:
        """Calculates documentation score using regex, as Clang does not do this."""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        if not non_empty_lines:
            return 0.0

        comment_lines = sum(1 for line in non_empty_lines if line.strip().startswith(('//', '/*', '*/', '*')))
        comment_ratio = comment_lines / len(non_empty_lines)
        comment_ratio_score = min(1.0, comment_ratio / 0.2) # 20% comment ratio gives a perfect score

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
        """
        Performs a hybrid analysis to generate code quality metrics.
        """
        # --- 1. Run Clang-Tidy Analysis ---
        clang_results = self.clang_analyzer.analyze_code_detailed(code)

        # --- 2. Calculate Scores from Clang issues ---
        style_score = 1.0
        maintainability_score = 1.0

        if "issues" in clang_results and clang_results["issues"]:
            issues = clang_results["issues"]
            style_penalty = 0.0
            maintainability_penalty = 0.0

            for issue in issues:
                category = issue.get('category')
                # Penalize more for errors than warnings
                penalty_amount = 0.15 if issue.get('severity') == 'error' else 0.05

                if category == 'style':
                    style_penalty += penalty_amount
                # Maintainability is affected by several categories
                elif category in ['maintainability', 'performance', 'security']:
                    maintainability_penalty += penalty_amount
            
            style_score = max(0.0, 1.0 - style_penalty)
            maintainability_score = max(0.0, 1.0 - maintainability_penalty)

        # --- 3. Calculate Documentation Score using Regex ---
        documentation_score = self._calculate_documentation_score(code)

        # --- 4. Return the final, combined metrics ---
        return {
            "style_compliance": round(style_score, 2),
            "documentation": round(documentation_score, 2),
            "maintainability": round(maintainability_score, 2)
        }

# --- Example Usage ---
if __name__ == '__main__':
    # This example code has some issues clang-tidy will find
    sample_driver_code = """
    #include <linux/module.h>
    
    // A function with a comment
    int documented_function(int p) {
        if(p > 10) // Missing braces
             return 1;
        return 0;
    }

    /* Missing function comment here */
    int undocumented_function() {
        int x = 5; // This variable is unused (bugprone-unused-variable)
        return 0;
    }
    """
    
    
    quality_analyzer = HybridCodeQualityAnalyzer()
    quality_report = quality_analyzer.evaluate(sample_driver_code)
    
    print("Code Quality Report:")
    print(quality_report)
    
