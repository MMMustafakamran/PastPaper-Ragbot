import os

# Directory containing the page files
input_dir = r"data/output/OCR/FAST/FAST ENTRY TEST PAST PAPERS PLSPOT_watermark"

def combine_pages(start_page, end_page, output_filename):
    """Combine pages from start_page to end_page (inclusive) into a single file."""
    output_file = os.path.join(input_dir, output_filename)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"\nCombining pages {start_page:03d} to {end_page:03d}...")
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for page_num in range(start_page, end_page + 1):
            page_file = os.path.join(input_dir, f"page_{page_num:03d}.txt")
            
            if os.path.exists(page_file):
                print(f"Reading {os.path.basename(page_file)}...")
                with open(page_file, 'r', encoding='utf-8') as infile:
                    # Write page separator
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"PAGE {page_num:03d}\n")
                    outfile.write(f"{'='*80}\n\n")
                    
                    # Write page content
                    content = infile.read()
                    outfile.write(content)
                    
                    # Add newline at end if not present
                    if not content.endswith('\n'):
                        outfile.write('\n')
            else:
                print(f"Warning: {os.path.basename(page_file)} not found, skipping...")
    
    print(f"Combined file created: {output_file}")

# Combine pages 1-17
combine_pages(1, 17, "combined_pages_001_to_017.txt")

# Combine pages 18-36
combine_pages(18, 36, "combined_pages_018_to_036.txt")

# Combine pages 37-55
combine_pages(37, 55, "combined_pages_037_to_055.txt")

print("\nAll files created successfully!")

