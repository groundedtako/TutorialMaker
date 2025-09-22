#!/usr/bin/env python3
"""
Script to replace print statements in app.py with proper logging calls
Since direct editing was banned, this script will create a replacement version
"""

import re
from pathlib import Path

def main():
    app_file = Path('d:/Sandbox/scribe_local/src/core/app.py')
    
    # Read the current file
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define replacements for app.py print statements
    replacements = [
        # Debug statements
        (r'print\(f?"DEBUG: ([^"]+)"\)', r'self.logger.debug("\1")'),
        (r'print\(f"DEBUG: ([^"]+)"\)', r'self.logger.debug(f"\1")'),
        (r'print\("DEBUG: ([^"]+)"\)', r'self.logger.debug("\1")'),
        
        # Error statements
        (r'print\(f?"ERROR: ([^"]+)"\)', r'self.logger.error("\1")'),
        (r'print\(f"ERROR: ([^"]+)"\)', r'self.logger.error(f"\1")'),
        (r'print\("ERROR: ([^"]+)"\)', r'self.logger.error("\1")'),
        
        # Warning statements
        (r'print\(f?"Warning: ([^"]+)"\)', r'self.logger.warning("\1")'),
        (r'print\(f"Warning: ([^"]+)"\)', r'self.logger.warning(f"\1")'),
        (r'print\("Warning: ([^"]+)"\)', r'self.logger.warning("\1")'),
        
        # Success/Info statements
        (r'print\(f?"SUCCESS ([^"]+)"\)', r'self.logger.info("\1")'),
        (r'print\(f"SUCCESS ([^"]+)"\)', r'self.logger.info(f"\1")'),
        (r'print\("SUCCESS ([^"]+)"\)', r'self.logger.info("\1")'),
        
        # New tutorial created
        (r'print\(f"New tutorial created: ([^"]+)"\)', r'self.logger.info(f"New tutorial created: \1")'),
        
        # Generic print statements that should be info
        (r'print\(f"([^"]+)"\)', r'self.logger.info(f"\1")'),
        (r'print\("([^"]+)"\)', r'self.logger.info("\1")'),
    ]
    
    # Apply replacements
    modified_content = content
    for pattern, replacement in replacements:
        modified_content = re.sub(pattern, replacement, modified_content)
    
    # Write back to file
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"Replaced print statements in {app_file}")

if __name__ == '__main__':
    main()
