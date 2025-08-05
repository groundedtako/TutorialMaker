#!/usr/bin/env python3
"""
Command-line script to export existing tutorials
"""

import sys
import argparse
from pathlib import Path

# Add src to path so we can import our modules
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.app import TutorialMakerApp

def main():
    parser = argparse.ArgumentParser(description="Export TutorialMaker tutorials")
    parser.add_argument("--tutorial-id", type=str, help="Specific tutorial ID to export")
    parser.add_argument("--formats", nargs="+", choices=["html", "word", "pdf"], 
                        default=["html", "word"], help="Export formats")
    parser.add_argument("--list", action="store_true", help="List available tutorials")
    parser.add_argument("--all", action="store_true", help="Export all tutorials")
    
    args = parser.parse_args()
    
    # Initialize app
    app = TutorialMakerApp()
    
    if args.list:
        # List all tutorials
        tutorials = app.list_tutorials()
        if not tutorials:
            print("No tutorials found.")
            return
        
        print(f"Found {len(tutorials)} tutorials:")
        for tutorial in tutorials:
            print(f"  {tutorial.title} ({tutorial.tutorial_id[:8]}) - {tutorial.step_count} steps")
        return
    
    if args.all:
        # Export all tutorials
        print(f"Exporting all tutorials to formats: {', '.join(args.formats)}")
        results = app.export_all_tutorials(args.formats)
        
        for tutorial_id, export_results in results.items():
            print(f"\nTutorial {tutorial_id[:8]}:")
            for format_name, result in export_results.items():
                if result.startswith("Error:"):
                    print(f"  {format_name}: {result}")
                else:
                    print(f"  {format_name}: {result}")
        return
    
    if args.tutorial_id:
        # Export specific tutorial
        print(f"Exporting tutorial {args.tutorial_id[:8]} to formats: {', '.join(args.formats)}")
        try:
            results = app.export_tutorial(args.tutorial_id, args.formats)
            print(f"\nExport results:")
            for format_name, result in results.items():
                if result.startswith("Error:"):
                    print(f"  {format_name}: {result}")
                else:
                    print(f"  {format_name}: {result}")
        except Exception as e:
            print(f"Export failed: {e}")
        return
    
    # No specific action - show help
    parser.print_help()

if __name__ == "__main__":
    main()