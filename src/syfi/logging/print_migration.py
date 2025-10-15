"""
Print Statement Migration Utility

Scans the codebase for print statements and provides automated migration
to structured logging with appropriate context and categorization.
"""
import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

try:
    from ..logging import get_logger, LogCategory
except ImportError:
    # Handle running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.syfi.logging import get_logger, LogCategory


@dataclass
class PrintStatementMatch:
    """Represents a found print statement."""
    file_path: str
    line_number: int
    line_content: str
    print_args: List[str]
    suggested_replacement: str
    suggested_log_level: str
    suggested_category: LogCategory
    context_hint: str


class PrintStatementScanner:
    """Scans Python files for print statements and suggests structured logging replacements."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.logger = get_logger(__name__)
        
        # Pattern matching for different types of print statements
        self.log_level_patterns = {
            'debug': [r'debug', r'trace', r'verbose'],
            'info': [r'info', r'status', r'progress', r'start', r'complete', r'success'],
            'warning': [r'warn', r'caution', r'alert', r'deprecated'],
            'error': [r'error', r'fail', r'exception', r'critical', r'fatal']
        }
        
        # Category detection patterns
        self.category_patterns = {
            LogCategory.DATABASE: [r'database', r'db', r'sql', r'query', r'connection'],
            LogCategory.SECURITY: [r'security', r'auth', r'permission', r'access', r'token'],
            LogCategory.PERFORMANCE: [r'performance', r'timing', r'speed', r'benchmark', r'profile'],
            LogCategory.AUDIT: [r'audit', r'log', r'track', r'record'],
            LogCategory.DATA_GENERATION: [r'generate', r'create', r'build', r'profile'],
            LogCategory.EXPORT: [r'export', r'save', r'write', r'output'],
            LogCategory.VALIDATION: [r'validate', r'check', r'verify', r'test']
        }
    
    def scan_directory(self, exclude_dirs: List[str] = None) -> List[PrintStatementMatch]:
        """Scan directory for Python files containing print statements."""
        if exclude_dirs is None:
            exclude_dirs = ['__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules']
        
        matches = []
        
        for py_file in self.root_path.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in str(py_file) for excluded in exclude_dirs):
                continue
            
            try:
                file_matches = self.scan_file(py_file)
                matches.extend(file_matches)
            except Exception as e:
                self.logger.warning(f"Error scanning {py_file}: {e}")
        
        return matches
    
    def scan_file(self, file_path: Path) -> List[PrintStatementMatch]:
        """Scan a single file for print statements."""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse AST to find print statements
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if it's a print function call
                    if (isinstance(node.func, ast.Name) and node.func.id == 'print'):
                        line_num = node.lineno
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        # Extract print arguments
                        print_args = self._extract_print_args(node)
                        
                        # Analyze context and suggest replacement
                        suggested_replacement, log_level, category, context_hint = self._analyze_print_statement(
                            file_path, line_content, print_args
                        )
                        
                        match = PrintStatementMatch(
                            file_path=str(file_path),
                            line_number=line_num,
                            line_content=line_content.strip(),
                            print_args=print_args,
                            suggested_replacement=suggested_replacement,
                            suggested_log_level=log_level,
                            suggested_category=category,
                            context_hint=context_hint
                        )
                        
                        matches.append(match)
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
        
        return matches
    
    def _extract_print_args(self, print_node: ast.Call) -> List[str]:
        """Extract arguments from print function call."""
        args = []
        
        for arg in print_node.args:
            if isinstance(arg, ast.Constant):
                args.append(repr(arg.value))
            elif isinstance(arg, ast.Name):
                args.append(arg.id)
            elif isinstance(arg, ast.Attribute):
                args.append(f"{arg.value.id if isinstance(arg.value, ast.Name) else '...'}.{arg.attr}")
            elif isinstance(arg, ast.Call):
                if isinstance(arg.func, ast.Name):
                    args.append(f"{arg.func.id}(...)")
                else:
                    args.append("function_call(...)")
            elif isinstance(arg, ast.JoinedStr):  # f-string
                args.append("f'...'")
            else:
                args.append("...")
        
        return args
    
    def _analyze_print_statement(self, file_path: Path, line_content: str, 
                                print_args: List[str]) -> Tuple[str, str, LogCategory, str]:
        """Analyze print statement and suggest appropriate logging replacement."""
        
        # Combine all text for analysis
        analysis_text = f"{file_path.stem} {line_content} {' '.join(print_args)}".lower()
        
        # Determine log level
        log_level = 'info'  # default
        for level, patterns in self.log_level_patterns.items():
            if any(re.search(pattern, analysis_text, re.IGNORECASE) for pattern in patterns):
                log_level = level
                break
        
        # Determine category
        category = LogCategory.SYSTEM  # default
        for cat, patterns in self.category_patterns.items():
            if any(re.search(pattern, analysis_text, re.IGNORECASE) for pattern in patterns):
                category = cat
                break
        
        # Generate suggested replacement
        logger_name = f"logger"
        
        # Analyze print arguments to construct logging call
        if len(print_args) == 1:
            # Simple case: single argument
            arg = print_args[0]
            if arg.startswith("'") or arg.startswith('"'):
                # String literal
                message = arg
                suggested_replacement = f"{logger_name}.{log_level}({message})"
            elif 'f"' in arg or "f'" in arg:
                # f-string - needs manual conversion
                suggested_replacement = f"{logger_name}.{log_level}(\"[Message needs manual conversion from f-string]\")"
            else:
                # Variable
                suggested_replacement = f"{logger_name}.{log_level}(f\"Value: {{{arg}}}\")"
        
        elif len(print_args) > 1:
            # Multiple arguments - suggest structured logging
            first_arg = print_args[0]
            other_args = print_args[1:]
            
            if first_arg.startswith("'") or first_arg.startswith('"'):
                # First arg is message, others are data
                message = first_arg
                extra_data = ", ".join([f"{arg}={arg}" for arg in other_args if not arg.startswith(("'", '"'))])
                if extra_data:
                    suggested_replacement = f"{logger_name}.{log_level}({message}, {extra_data})"
                else:
                    suggested_replacement = f"{logger_name}.{log_level}({message})"
            else:
                # All arguments are data
                data_pairs = ", ".join([f"value_{i}={arg}" for i, arg in enumerate(print_args)])
                suggested_replacement = f"{logger_name}.{log_level}(\"Multiple values\", {data_pairs})"
        
        else:
            # Empty print
            suggested_replacement = f"{logger_name}.debug(\"Empty print statement\")"
        
        # Generate context hint
        context_hint = self._generate_context_hint(file_path, line_content, category)
        
        return suggested_replacement, log_level, category, context_hint
    
    def _generate_context_hint(self, file_path: Path, line_content: str, 
                              category: LogCategory) -> str:
        """Generate context hint for the replacement."""
        hints = []
        
        # File-based hints
        if 'test' in str(file_path):
            hints.append("Consider using pytest fixtures and assertions instead of print")
        elif 'main' in file_path.stem:
            hints.append("Main entry point - consider using info level")
        elif 'example' in str(file_path):
            hints.append("Example code - consider debug level")
        
        # Content-based hints
        if 'todo' in line_content.lower() or 'fixme' in line_content.lower():
            hints.append("TODO/FIXME comment - consider removing or using debug level")
        elif '=' in line_content and ('print(' in line_content):
            hints.append("Debugging statement - consider debug level with variable context")
        
        # Category-based hints
        category_hints = {
            LogCategory.DATABASE: "Add query and timing information to log context",
            LogCategory.SECURITY: "Ensure no sensitive data is logged",
            LogCategory.PERFORMANCE: "Consider using @log_performance decorator instead",
            LogCategory.AUDIT: "Use audit() method with structured data",
            LogCategory.DATA_GENERATION: "Include record counts and progress information",
            LogCategory.EXPORT: "Include file paths and export statistics"
        }
        
        if category in category_hints:
            hints.append(category_hints[category])
        
        return "; ".join(hints) if hints else "Standard logging replacement"
    
    def generate_migration_report(self, matches: List[PrintStatementMatch]) -> str:
        """Generate a comprehensive migration report."""
        if not matches:
            return "No print statements found in the codebase."
        
        report = []
        report.append("# Print Statement Migration Report")
        report.append(f"\nFound {len(matches)} print statements to migrate:\n")
        
        # Group by file
        files = {}
        for match in matches:
            if match.file_path not in files:
                files[match.file_path] = []
            files[match.file_path].append(match)
        
        for file_path, file_matches in files.items():
            report.append(f"## {file_path}")
            report.append(f"Found {len(file_matches)} print statements:\n")
            
            for match in file_matches:
                report.append(f"**Line {match.line_number}:** `{match.line_content}`")
                report.append(f"- **Suggested replacement:** `{match.suggested_replacement}`")
                report.append(f"- **Log level:** {match.suggested_log_level}")
                report.append(f"- **Category:** {match.suggested_category.value}")
                report.append(f"- **Context hint:** {match.context_hint}")
                report.append("")
        
        # Summary statistics
        report.append("\n## Summary Statistics")
        
        # By log level
        level_counts = {}
        for match in matches:
            level_counts[match.suggested_log_level] = level_counts.get(match.suggested_log_level, 0) + 1
        
        report.append("\n### By Log Level:")
        for level, count in sorted(level_counts.items()):
            report.append(f"- {level}: {count}")
        
        # By category
        category_counts = {}
        for match in matches:
            cat_name = match.suggested_category.value
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        
        report.append("\n### By Category:")
        for category, count in sorted(category_counts.items()):
            report.append(f"- {category}: {count}")
        
        return "\n".join(report)
    
    def create_logger_import_suggestions(self, matches: List[PrintStatementMatch]) -> Dict[str, str]:
        """Create import suggestions for each file that needs migration."""
        files_needing_imports = {}
        
        for match in matches:
            if match.file_path not in files_needing_imports:
                # Determine most appropriate logger type for the file
                categories = [m.suggested_category for m in matches if m.file_path == match.file_path]
                most_common_category = max(set(categories), key=categories.count)
                
                # Generate import suggestion
                if most_common_category == LogCategory.DATABASE:
                    import_suggestion = "from src.syfi.logging import get_database_logger\nlogger = get_database_logger(__name__)"
                elif most_common_category == LogCategory.SECURITY:
                    import_suggestion = "from src.syfi.logging import get_security_logger\nlogger = get_security_logger(__name__)"
                elif most_common_category == LogCategory.PERFORMANCE:
                    import_suggestion = "from src.syfi.logging import get_performance_logger\nlogger = get_performance_logger(__name__)"
                else:
                    import_suggestion = "from src.syfi.logging import get_logger\nlogger = get_logger(__name__)"
                
                files_needing_imports[match.file_path] = import_suggestion
        
        return files_needing_imports


# CLI utility functions

def scan_and_report(root_path: str = ".") -> str:
    """Scan codebase and generate migration report."""
    scanner = PrintStatementScanner(root_path)
    matches = scanner.scan_directory()
    return scanner.generate_migration_report(matches)


def scan_and_get_matches(root_path: str = ".") -> List[PrintStatementMatch]:
    """Scan codebase and return matches for programmatic processing."""
    scanner = PrintStatementScanner(root_path)
    return scanner.scan_directory()


if __name__ == "__main__":
    # Run scan on current directory
    import sys
    
    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    report = scan_and_report(root_path)
    print(report)