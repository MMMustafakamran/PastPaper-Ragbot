#!/usr/bin/env python3
"""
Past Papers RAG Chatbot - Main Entry Point
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.parser import QuestionParser, main as parse_main

def main():
    """Main entry point for the application"""
    print("🎓 Past Papers RAG Chatbot")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "parse":
            print("📄 Parsing PDF and extracting questions...")
            parse_main()
        elif command == "help":
            print_help()
        else:
            print(f"❌ Unknown command: {command}")
            print_help()
    else:
        print_help()

def print_help():
    """Print help information"""
    print("""
Usage: python main.py <command>

Commands:
  parse    - Parse PDF and extract questions
  help     - Show this help message

Examples:
  python main.py parse
  python main.py help
""")

if __name__ == "__main__":
    main()
