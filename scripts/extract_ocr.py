#!/usr/bin/env python3
"""
OCR Extraction Workflow
Converts OCR images to text and prepares for Standard_text/
"""

import sys
from pathlib import Path

def main():
    """Extract OCR images"""
    print("="*60)
    print("OCR IMAGE TO TEXT CONVERSION")
    print("="*60)
    print()
    print("This uses scripts/image_to_text.py")
    print()
    print("Usage:")
    print("  python scripts/image_to_text.py --filter NET")
    print("  python scripts/image_to_text.py --filter FAST")
    print()
    print("NEXT STEPS:")
    print("1. Review extracted text in: data/output/OCR/")
    print("2. Clean/format manually or with scripts")
    print("3. Copy final files to: data/Standard_text/")
    print("="*60)

if __name__ == "__main__":
    main()


