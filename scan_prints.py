"""
Standalone Print Statement Scanner

Simple scanner to find print statements in the codebase without dependencies.
"""
import ast
import os
from pathlib import Path
from typing import List, Tuple


def scan_for_prints(root_path: str) -> List[Tuple[str, int, str]]:
    """
    Scan for print statements in Python files.
    
    Returns:
        List of (file_path, line_number, line_content) tuples
    """
    print_statements = []
    exclude_dirs = ['__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules']
    
    for py_file in Path(root_path).rglob('*.py'):
        # Skip excluded directories
        if any(excluded in str(py_file) for excluded in exclude_dirs):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse AST to find print statements
            try:
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # Check if it's a print function call
                        if (isinstance(node.func, ast.Name) and node.func.id == 'print'):
                            line_num = node.lineno
                            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                            
                            print_statements.append((
                                str(py_file.relative_to(root_path)),
                                line_num,
                                line_content.strip()
                            ))
            
            except SyntaxError:
                # Skip files with syntax errors
                continue
                
        except Exception:
            # Skip files that can't be read
            continue
    
    return print_statements


def generate_report(print_statements: List[Tuple[str, int, str]]) -> str:
    """Generate a simple report of print statements."""
    if not print_statements:
        return "✅ No print statements found in the codebase!"
    
    report = []
    report.append(f"# Print Statement Migration Report")
    report.append(f"\n🔍 Found {len(print_statements)} print statements:\n")
    
    # Group by file
    files = {}
    for file_path, line_num, line_content in print_statements:
        if file_path not in files:
            files[file_path] = []
        files[file_path].append((line_num, line_content))
    
    for file_path, statements in sorted(files.items()):
        report.append(f"## 📄 {file_path}")
        report.append(f"Found {len(statements)} print statements:")
        
        for line_num, line_content in sorted(statements):
            report.append(f"  - Line {line_num}: `{line_content}`")
        
        report.append("")
    
    # Summary
    report.append(f"\n## 📊 Summary")
    report.append(f"- Total files with print statements: {len(files)}")
    report.append(f"- Total print statements to migrate: {len(print_statements)}")
    
    # Priority files (main modules)
    priority_files = [f for f in files.keys() if any(x in f for x in ['main.py', 'web_browser.py', 'syfi_cli.py'])]
    if priority_files:
        report.append(f"\n## 🎯 Priority Files:")
        for file_path in priority_files:
            count = len(files[file_path])
            report.append(f"  - {file_path}: {count} statements")
    
    return "\n".join(report)


if __name__ == "__main__":
    import sys
    
    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    statements = scan_for_prints(root_path)
    report = generate_report(statements)
    print(report)