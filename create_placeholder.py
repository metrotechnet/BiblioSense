#!/usr/bin/env python3
"""
Script to create a placeholder book cover image
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_book_placeholder():
    # Image dimensions (typical book cover ratio)
    width, height = 150, 200
    
    # Create a new image with a light gray background
    img = Image.new('RGB', (width, height), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Draw a border
    border_color = '#cccccc'
    draw.rectangle([2, 2, width-3, height-3], outline=border_color, width=2)
    
    # Draw a book icon (simple rectangle with lines)
    book_x = width // 4
    book_y = height // 4
    book_width = width // 2
    book_height = height // 2
    
    # Book cover
    draw.rectangle([book_x, book_y, book_x + book_width, book_y + book_height], 
                  fill='#e0e0e0', outline='#999999', width=2)
    
    # Book spine lines
    spine_x = book_x + 10
    for i in range(3):
        y_pos = book_y + 15 + (i * 20)
        draw.line([spine_x, y_pos, spine_x + book_width - 20, y_pos], 
                 fill='#999999', width=1)
    
    # Try to add text (fallback if font is not available)
    try:
        # Try to use a default font
        font = ImageFont.load_default()
        text = "LIVRE"
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        text_x = (width - text_width) // 2
        text_y = book_y + book_height + 20
        
        draw.text((text_x, text_y), text, fill='#666666', font=font)
        
    except Exception:
        # If font loading fails, just add simple text
        draw.text((width//2 - 20, book_y + book_height + 20), "LIVRE", fill='#666666')
    
    # Save the image
    output_path = "static/images/placeholder.png"
    img.save(output_path, "PNG")
    print(f"Placeholder image created: {output_path}")

if __name__ == "__main__":
    create_book_placeholder()
