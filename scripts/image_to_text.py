#!/usr/bin/env python3
"""
Image to Text Converter using GPT-5 Nano
Processes images recursively and extracts text using OpenAI's vision API.
"""

import os
import json
import base64
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def load_config():
    """Load API key from config.json"""
    # Try config/config.json first, then fallback to config.json in parent
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"config.json not found. Expected at: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    api_key = config.get("apiKey")
    if not api_key or api_key == "your-openai-api-key-here":
        raise ValueError("Please set your OpenAI API key in config.json")
    
    return api_key


def find_all_images(root_dir):
    """Recursively find all PNG images in the directory"""
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")
    
    images = list(root_path.rglob("*.png"))
    return sorted(images)


def encode_image(image_path):
    """Read and encode image as base64"""
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        file_size = len(image_data)
        base64_data = base64.b64encode(image_data).decode('utf-8')
        base64_size = len(base64_data)
        return base64_data, file_size, base64_size


def format_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def extract_text_from_image(client, image_path, model="gpt-5-nano"):
    """Send image to OpenAI API and extract text using GPT-5 nano ONLY"""
    start_time = time.time()
    
    # Enforce GPT-5 nano only - no fallback
    if model != "gpt-5-nano":
        raise ValueError(f"Only GPT-5 nano is allowed. Model '{model}' is not permitted.")
    
    # Encode image
    print(f"  └─ Reading image file...")
    base64_image, file_size, base64_size = encode_image(image_path)
    print(f"  └─ Image size: {format_size(file_size)} ({file_size:,} bytes)")
    print(f"  └─ Base64 encoded size: {format_size(base64_size)} ({base64_size:,} bytes)")
    
    print(f"  └─ Sending request to OpenAI API (model: {model})...")
    api_start = time.time()
    
    # Call OpenAI API with vision capabilities - GPT-5 nano ONLY
    # Note: gpt-5-nano uses max_completion_tokens instead of max_tokens
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract all text from this exam paper image. This is a past paper containing multiple-choice questions (MCQs).

CRITICAL REQUIREMENTS:
1. Preserve question numbering exactly as shown (e.g., "1)", "Q.1", "1.")
2. Preserve option labels exactly (A., B., C., D. or A), B), C), D))
3. Preserve answer markers if present:
   - "(Correct)" markers after options (NET format)
   - Answer keys at the end of sections
4. Maintain line breaks between questions and options
5. Preserve mathematical notation, formulas, and special characters
6. Keep option text on separate lines when possible
7. Do NOT combine multiple options on one line unless they appear that way in the image

FORMAT PRESERVATION:
- If options appear inline (e.g., "A) text1. C) text2."), preserve that format
- If options appear on separate lines, keep them separate
- Preserve any answer key sections at the end
- Maintain spacing and indentation that helps identify question boundaries

Return the extracted text exactly as it appears, preserving all structural elements needed for parsing questions, options, and correct answers."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_completion_tokens=4096
    )
    
    api_time = time.time() - api_start
    
    # Verify the model used is GPT-5 nano
    model_used = response.model
    if "gpt-5-nano" not in model_used.lower():
        raise ValueError(f"ERROR: Expected GPT-5 nano but received model '{model_used}'. Aborting.")
    
    # Extract text from response
    text = response.choices[0].message.content
    text_length = len(text)
    text_words = len(text.split())
    
    # Get API response details
    tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else "N/A"
    prompt_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else "N/A"
    completion_tokens = response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else "N/A"
    
    total_time = time.time() - start_time
    
    print(f"  └─ ✓ API Response received in {api_time:.2f}s")
    print(f"  └─ Model used: {model_used} ✓")
    print(f"  └─ Tokens: {tokens_used} total (prompt: {prompt_tokens}, completion: {completion_tokens})")
    print(f"  └─ Extracted text: {text_length:,} characters, {text_words:,} words")
    print(f"  └─ Total processing time: {total_time:.2f}s")
    
    return {
        'text': text,
        'model': model_used,
        'tokens': tokens_used,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'processing_time': total_time,
        'text_length': text_length,
        'text_words': text_words
    }


def create_output_path(input_path, output_root):
    """Create output path mirroring input structure"""
    # Get relative path from OCR_Images
    input_path = Path(input_path)
    
    # Find data/images in the path
    parts = input_path.parts
    try:
        # Look for "images" folder (could be data/images or just images)
        images_index = None
        for i, part in enumerate(parts):
            if part == "images":
                images_index = i
                break
        if images_index is not None:
            # Get path after images folder
            relative_parts = parts[images_index + 1:]
        else:
            # If images not in path, use entire relative path
            relative_parts = input_path.parts
    except (ValueError, IndexError):
        # Fallback: use entire relative path
        relative_parts = input_path.parts
    
    # Create output path
    output_path = Path(output_root) / Path(*relative_parts)
    # Change extension to .txt
    output_path = output_path.with_suffix('.txt')
    
    return output_path


def process_images(limit=None):
    """Main function to process all images
    
    Args:
        limit: Maximum number of images to process (None for all)
    """
    overall_start = time.time()
    start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 70)
    print("IMAGE TO TEXT CONVERTER - GPT-5 Nano")
    if limit:
        print(f"TEST MODE: Processing first {limit} image(s) only")
    else:
        print("PROCESSING ALL IMAGES")
    print("=" * 70)
    print(f"Start time: {start_datetime}")
    print()
    
    # Load configuration
    print("Loading configuration...")
    try:
        api_key = load_config()
        print(f"  └─ ✓ Configuration loaded successfully")
        print(f"  └─ API Key: {'*' * (len(api_key) - 8) + api_key[-8:] if len(api_key) > 8 else '***'}")
    except Exception as e:
        print(f"  └─ ✗ Configuration error: {str(e)}")
        raise
    
    print()
    print("Initializing OpenAI client...")
    client = OpenAI(api_key=api_key)
    print("  └─ ✓ OpenAI client initialized")
    print()
    
    # Verify model exists
    print("Verifying model availability...")
    try:
        models = client.models.list()
        available_models = [model.id for model in models.data]
        
        print(f"  └─ Found {len(available_models)} available model(s)")
        
        # Check if gpt-5-nano exists
        model_name = "gpt-5-nano"
        model_found = False
        matching_models = []
        
        for model_id in available_models:
            if model_name.lower() in model_id.lower():
                model_found = True
                matching_models.append(model_id)
        
        if model_found:
            print(f"  └─ ✓ Model '{model_name}' found:")
            for model_id in matching_models:
                print(f"      • {model_id}")
        else:
            print(f"  └─ ⚠ Model '{model_name}' not found in available models")
            print(f"  └─ Available vision models:")
            vision_models = [m for m in available_models if 'vision' in m.lower() or 'gpt-4' in m.lower() or 'gpt-3.5' in m.lower()]
            if vision_models:
                for model_id in vision_models[:10]:  # Show first 10
                    print(f"      • {model_id}")
            else:
                print(f"      (No obvious vision models found)")
                print(f"  └─ First 10 available models:")
                for model_id in available_models[:10]:
                    print(f"      • {model_id}")
        
        print()
    except Exception as e:
        print(f"  └─ ⚠ Could not verify models: {str(e)}")
        print(f"  └─ Continuing anyway...")
        print()
    
    # Set directories
    input_dir = Path("data/images")
    output_dir = Path("data/output")
    
    print(f"Input directory: {input_dir.absolute()}")
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    # Find all images
    print("Scanning for images...")
    images = find_all_images(input_dir)
    total_found = len(images)
    
    if total_found == 0:
        print(f"  └─ ✗ No PNG images found in {input_dir} directory")
        return
    
    # Apply limit if specified
    if limit:
        images = images[:limit]
        total = len(images)
        print(f"  └─ ✓ Found {total_found} PNG image(s) total")
        print(f"  └─ ⚠ TEST MODE: Processing first {total} image(s) only")
    else:
        total = total_found
        print(f"  └─ ✓ Found {total} PNG image(s)")
    
    # Group images by folder for display
    folders = {}
    for img in images:
        folder = str(img.parent)
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(img.name)
    
    print(f"  └─ Images found in {len(folders)} folder(s):")
    for folder, files in sorted(folders.items()):
        print(f"      • {folder}: {len(files)} image(s)")
    
    print()
    print("=" * 70)
    print("STARTING PROCESSING")
    print("=" * 70)
    print()
    
    # Process each image
    successful = 0
    failed = 0
    total_tokens = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_text_chars = 0
    total_text_words = 0
    total_processing_time = 0
    models_used = {}
    
    for i, image_path in enumerate(images, 1):
        print(f"[{i}/{total}] {'=' * 60}")
        print(f"Image: {image_path}")
        print(f"Relative path: {image_path.relative_to(input_dir)}")
        print()
        
        # Extract text - GPT-5 nano ONLY, no fallback
        try:
            result = extract_text_from_image(client, image_path)
        except Exception as e:
            print(f"  └─ ✗ FAILED: {str(e)}")
            print(f"  └─ Error type: {type(e).__name__}")
            print(f"  └─ GPT-5 nano is required. Aborting this image.")
            failed += 1
            print()
            continue
        
        if result is None:
            print(f"  └─ ✗ FAILED: Could not extract text from image")
            failed += 1
            print()
            continue
        
        # Update statistics
        if isinstance(result.get('tokens'), int):
            total_tokens += result['tokens']
        if isinstance(result.get('prompt_tokens'), int):
            total_prompt_tokens += result['prompt_tokens']
        if isinstance(result.get('completion_tokens'), int):
            total_completion_tokens += result['completion_tokens']
        total_text_chars += result['text_length']
        total_text_words += result['text_words']
        total_processing_time += result['processing_time']
        
        model = result['model']
        models_used[model] = models_used.get(model, 0) + 1
        
        # Create output path
        output_path = create_output_path(image_path, output_dir)
        print(f"  └─ Output path: {output_path}")
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  └─ Output directory: {output_path.parent}")
        
        # Write text to file
        try:
            write_start = time.time()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            write_time = time.time() - write_start
            file_size = output_path.stat().st_size
            
            print(f"  └─ ✓ File saved successfully")
            print(f"  └─ Output file size: {format_size(file_size)} ({file_size:,} bytes)")
            print(f"  └─ Write time: {write_time:.3f}s")
            successful += 1
        except Exception as e:
            print(f"  └─ ✗ Error saving file: {str(e)}")
            print(f"  └─ Error type: {type(e).__name__}")
            failed += 1
        
        print()
    
    # Calculate overall statistics
    overall_time = time.time() - overall_start
    end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    avg_time_per_image = total_processing_time / successful if successful > 0 else 0
    
    # Summary
    print()
    print("=" * 70)
    print("PROCESSING COMPLETE - SUMMARY")
    print("=" * 70)
    print(f"End time: {end_datetime}")
    print(f"Total elapsed time: {overall_time:.2f}s ({overall_time/60:.2f} minutes)")
    print()
    print("Results:")
    print(f"  • Total images processed: {total}")
    if limit and total_found > total:
        print(f"  • Remaining images: {total_found - total} (not processed in test mode)")
    print(f"  • Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"  • Failed: {failed} ({failed/total*100:.1f}%)")
    print()
    
    if successful > 0:
        print("Statistics:")
        print(f"  • Average processing time per image: {avg_time_per_image:.2f}s")
        print(f"  • Total text extracted: {total_text_chars:,} characters")
        print(f"  • Total words extracted: {total_text_words:,} words")
        print(f"  • Average characters per image: {total_text_chars/successful:,.0f}")
        print(f"  • Average words per image: {total_text_words/successful:,.0f}")
        print()
        
        if total_tokens > 0:
            print("API Usage:")
            print(f"  • Total tokens used: {total_tokens:,}")
            print(f"  • Prompt tokens: {total_prompt_tokens:,}")
            print(f"  • Completion tokens: {total_completion_tokens:,}")
            print(f"  • Average tokens per image: {total_tokens/successful:,.0f}")
            print()
        
        print("Models used:")
        for model, count in sorted(models_used.items()):
            print(f"  • {model}: {count} image(s) ({count/successful*100:.1f}%)")
        print()
    
    print(f"Output directory: {output_dir.absolute()}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert images to text using GPT-5 Nano vision API"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Limit the number of images to process (default: 3 for testing, use --limit 0 or --limit None for all)"
    )
    
    args = parser.parse_args()
    
    # Handle special case: --limit 0 or --limit None means process all
    limit = None if args.limit == 0 else args.limit
    
    try:
        process_images(limit=limit)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

