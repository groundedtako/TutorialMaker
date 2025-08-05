#!/usr/bin/env python3
"""
Simple test script for export functionality without full app dependencies
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.storage import TutorialStorage, TutorialMetadata, TutorialStep
from src.core.exporters import TutorialExporter

def main():
    print("Testing export functionality...")
    
    # Initialize storage
    storage = TutorialStorage()
    exporter = TutorialExporter(storage)
    
    # List tutorials
    tutorials = storage.list_tutorials()
    if not tutorials:
        print("No tutorials found.")
        return
    
    print(f"Found {len(tutorials)} tutorials:")
    for tutorial in tutorials:
        print(f"  {tutorial.title} ({tutorial.tutorial_id[:8]}) - {tutorial.step_count} steps")
    
    # Export the first tutorial
    tutorial = tutorials[0]
    print(f"\nExporting tutorial: {tutorial.title}")
    
    try:
        results = exporter.export_tutorial(tutorial.tutorial_id, ['html', 'word'])
        print("Export results:")
        for format_name, result in results.items():
            if result.startswith("Error:"):
                print(f"  {format_name}: {result}")
            else:
                print(f"  {format_name}: {result}")
                
                # Check if file exists
                if Path(result).exists():
                    size = Path(result).stat().st_size
                    print(f"    File size: {size} bytes")
                
    except Exception as e:
        print(f"Export failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()