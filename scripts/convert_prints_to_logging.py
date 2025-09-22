#!/usr/bin/env python3
"""
Script to systematically convert print statements to proper logging calls
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

def analyze_print_statement(line: str) -> Tuple[str, str]:
    """
    Analyze a print statement and determine the appropriate logging level
    
    Returns:
        (logging_level, cleaned_message)
    """
    line_lower = line.lower()
    
    # Determine logging level based on content
    if any(keyword in line_lower for keyword in ['error', 'failed', 'exception', 'traceback']):
        level = 'error'
    elif any(keyword in line_lower for keyword in ['warning', 'warn']):
        level = 'warning'
    elif any(keyword in line_lower for keyword in ['debug:', 'debug ', 'debug-']):
        level = 'debug'
    elif any(keyword in line_lower for keyword in ['success', 'completed', 'finished', 'created', 'started']):
        level = 'info'
    else:
        # Default based on context
        if 'debug' in line_lower or line_lower.strip().startswith('print(f"debug'):
            level = 'debug'
        else:
            level = 'info'
    
    return level

def convert_print_to_logging(line: str, logger_var: str = 'self.logger') -> str:
    """
    Convert a print statement to appropriate logging call
    """
    # Extract the content inside print()
    print_match = re.search(r'print\((.*)\)', line)
    if not print_match:
        return line
    
    print_content = print_match.group(1)
    level = analyze_print_statement(line)
    
    # Clean up DEBUG: prefixes since logging will handle levels
    if print_content.startswith('"DEBUG: ') or print_content.startswith("'DEBUG: "):
        quote_char = print_content[0]
        print_content = quote_char + print_content[8:]  # Remove 'DEBUG: '
    elif print_content.startswith('f"DEBUG: ') or print_content.startswith("f'DEBUG: "):
        quote_char = print_content[1]
        print_content = 'f' + quote_char + print_content[9:]  # Remove 'DEBUG: '
    
    # Replace the print statement
    indent = line[:len(line) - len(line.lstrip())]
    converted = f"{indent}{logger_var}.{level}({print_content})"
    
    return converted

def get_logger_import_and_var(file_path: Path) -> Tuple[str, str]:
    """
    Determine the appropriate logger import and variable name for a file
    """
    relative_path = file_path.relative_to(Path('d:/Sandbox/scribe_local'))
    
    if relative_path.parts[0] == 'src':
        # Core modules - use existing logger
        if len(relative_path.parts) >= 3:
            module_path = '.'.join(relative_path.parts[1:-1]) + '.' + relative_path.stem
            return f"from ..core.logger import get_logger", f"get_logger('{module_path}')"
        else:
            return f"from .logger import get_logger", f"get_logger('{relative_path.stem}')"
    elif relative_path.parts[0] == 'tests':
        return "from src.core.logger import get_logger", f"get_logger('tests.{relative_path.stem}')"
    else:
        return "from src.core.logger import get_logger", f"get_logger('{relative_path.stem}')"

def process_file(file_path: Path) -> Dict[str, any]:
    """
    Process a single Python file to convert print statements
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        converted_lines = []
        changes_made = []
        has_logger_import = False
        logger_var = None
        
        # Check if file already has logger setup
        for i, line in enumerate(lines):
            if 'get_logger' in line and 'import' in line:
                has_logger_import = True
            if 'self.logger = get_logger(' in line:
                logger_var = 'self.logger'
            elif 'logger = get_logger(' in line:
                logger_var = 'logger'
        
        # If no logger setup, determine what we need
        if not has_logger_import:
            import_line, logger_setup = get_logger_import_and_var(file_path)
            # Add import after existing imports
            import_added = False
            for i, line in enumerate(lines):
                converted_lines.append(line)
                if line.startswith('import ') or line.startswith('from ') and not import_added:
                    # Look ahead to find the end of imports
                    j = i + 1
                    while j < len(lines) and (lines[j].startswith('import ') or lines[j].startswith('from ') or lines[j].strip() == ''):
                        j += 1
                    if j == i + 1:  # This is the last import
                        converted_lines.append(f"{import_line}\n")
                        import_added = True
            
            if not import_added and converted_lines:
                converted_lines.insert(0, f"{import_line}\n")
        else:
            converted_lines = lines.copy()
        
        # Convert print statements
        for i, line in enumerate(converted_lines):
            if 'print(' in line and not line.strip().startswith('#'):
                if logger_var:
                    new_line = convert_print_to_logging(line, logger_var)
                else:
                    # Use module-level logger
                    new_line = convert_print_to_logging(line, 'get_logger()')
                
                if new_line != line:
                    changes_made.append({
                        'line_num': i + 1,
                        'old': line.strip(),
                        'new': new_line.strip()
                    })
                    converted_lines[i] = new_line
        
        return {
            'file_path': file_path,
            'changes': changes_made,
            'converted_lines': converted_lines,
            'success': True
        }
    
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e),
            'success': False
        }

def main():
    """Main conversion process"""
    base_path = Path('d:/Sandbox/scribe_local')
    
    # Find all Python files with print statements
    python_files = []
    for root, dirs, files in os.walk(base_path):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'venv', 'env']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'print(' in content:
                            python_files.append(file_path)
                except:
                    continue
    
    print(f"Found {len(python_files)} Python files with print statements")
    
    # Process each file
    results = []
    for file_path in python_files:
        print(f"Processing: {file_path.relative_to(base_path)}")
        result = process_file(file_path)
        results.append(result)
        
        if result['success'] and result['changes']:
            print(f"  - {len(result['changes'])} print statements converted")
            
            # Write the converted file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(result['converted_lines'])
                print(f"  - File updated successfully")
            except Exception as e:
                print(f"  - Error writing file: {e}")
        elif result['success']:
            print(f"  - No changes needed")
        else:
            print(f"  - Error: {result.get('error', 'Unknown error')}")
    
    # Summary
    total_changes = sum(len(r.get('changes', [])) for r in results if r['success'])
    successful_files = sum(1 for r in results if r['success'])
    
    print(f"\nConversion Summary:")
    print(f"- Files processed: {len(results)}")
    print(f"- Files successfully updated: {successful_files}")
    print(f"- Total print statements converted: {total_changes}")

if __name__ == '__main__':
    main()
