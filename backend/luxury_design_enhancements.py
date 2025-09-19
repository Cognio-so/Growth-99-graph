"""
Luxury Design Enhancement System
This module provides luxury fonts and colors to enhance UI generation
while keeping the JSON schema structure intact.
"""
import random
from llm import get_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

# Enhanced Luxury Font Combinations - More Stylish and Diverse
LUXURY_FONT_PALETTES = {
    "elegant_serif": {
        "headings": "font-family: 'Playfair Display', 'Georgia', serif",
        "subheadings": "font-family: 'Crimson Text', 'Times New Roman', serif", 
        "body": "font-family: 'Inter', 'Helvetica Neue', sans-serif",
        "accent": "font-family: 'Dancing Script', cursive",
        "google_fonts": ["Playfair+Display:wght@400;500;600;700", "Crimson+Text:wght@400;600", "Inter:wght@300;400;500;600", "Dancing+Script:wght@400;500"]
    },
    "modern_luxury": {
        "headings": "font-family: 'Montserrat', 'Arial', sans-serif",
        "subheadings": "font-family: 'Lora', 'Georgia', serif",
        "body": "font-family: 'Source Sans Pro', 'Helvetica', sans-serif", 
        "accent": "font-family: 'Great Vibes', cursive",
        "google_fonts": ["Montserrat:wght@300;400;500;600;700", "Lora:wght@400;500;600", "Source+Sans+Pro:wght@300;400;600", "Great+Vibes"]
    },
    "sophisticated_minimal": {
        "headings": "font-family: 'Poppins', 'Arial', sans-serif",
        "subheadings": "font-family: 'Merriweather', 'Georgia', serif",
        "body": "font-family: 'Open Sans', 'Helvetica', sans-serif",
        "accent": "font-family: 'Allura', cursive", 
        "google_fonts": ["Poppins:wght@300;400;500;600;700", "Merriweather:wght@300;400;700", "Open+Sans:wght@300;400;600", "Allura"]
    },
    "premium_corporate": {
        "headings": "font-family: 'Roboto Slab', 'Georgia', serif",
        "subheadings": "font-family: 'Nunito Sans', 'Arial', sans-serif", 
        "body": "font-family: 'IBM Plex Sans', 'Helvetica', sans-serif",
        "accent": "font-family: 'Satisfy', cursive",
        "google_fonts": ["Roboto+Slab:wght@300;400;500;700", "Nunito+Sans:wght@300;400;600;700", "IBM+Plex+Sans:wght@300;400;500", "Satisfy"]
    },
    "luxury_fashion": {
        "headings": "font-family: 'Cormorant Garamond', 'Georgia', serif",
        "subheadings": "font-family: 'Raleway', 'Arial', sans-serif",
        "body": "font-family: 'Lato', 'Helvetica', sans-serif",
        "accent": "font-family: 'Pacifico', cursive",
        "google_fonts": ["Cormorant+Garamond:wght@300;400;500;600", "Raleway:wght@300;400;500;600", "Lato:wght@300;400;700", "Pacifico"]
    },
    "stylish_modern": {
        "headings": "font-family: 'Oswald', 'Arial', sans-serif",
        "subheadings": "font-family: 'PT Serif', 'Georgia', serif",
        "body": "font-family: 'Work Sans', 'Helvetica', sans-serif",
        "accent": "font-family: 'Yellowtail', cursive",
        "google_fonts": ["Oswald:wght@300;400;500;600;700", "PT+Serif:wght@400;700", "Work+Sans:wght@300;400;500;600", "Yellowtail"]
    },
    "elegant_script": {
        "headings": "font-family: 'Abril Fatface', 'Georgia', serif",
        "subheadings": "font-family: 'Libre Baskerville', 'Times New Roman', serif",
        "body": "font-family: 'Nunito', 'Arial', sans-serif",
        "accent": "font-family: 'Kaushan Script', cursive",
        "google_fonts": ["Abril+Fatface", "Libre+Baskerville:wght@400;700", "Nunito:wght@300;400;600;700", "Kaushan+Script"]
    },
    "premium_tech": {
        "headings": "font-family: 'Orbitron', 'Arial', sans-serif",
        "subheadings": "font-family: 'Exo 2', 'Arial', sans-serif",
        "body": "font-family: 'Fira Sans', 'Helvetica', sans-serif",
        "accent": "font-family: 'Righteous', cursive",
        "google_fonts": ["Orbitron:wght@400;500;700;900", "Exo+2:wght@300;400;500;600", "Fira+Sans:wght@300;400;500;600", "Righteous"]
    },
    "luxury_editorial": {
        "headings": "font-family: 'Bebas Neue', 'Arial', sans-serif",
        "subheadings": "font-family: 'Lora', 'Georgia', serif",
        "body": "font-family: 'Source Sans Pro', 'Helvetica', sans-serif",
        "accent": "font-family: 'Amatic SC', cursive",
        "google_fonts": ["Bebas+Neue", "Lora:wght@400;500;600;700", "Source+Sans+Pro:wght@300;400;600;700", "Amatic+SC:wght@400;700"]
    },
    "sophisticated_serif": {
        "headings": "font-family: 'Cinzel', 'Georgia', serif",
        "subheadings": "font-family: 'Cormorant Garamond', 'Georgia', serif",
        "body": "font-family: 'Lato', 'Helvetica', sans-serif",
        "accent": "font-family: 'Alex Brush', cursive",
        "google_fonts": ["Cinzel:wght@400;500;600", "Cormorant+Garamond:wght@300;400;500;600", "Lato:wght@300;400;700", "Alex+Brush"]
    },
    "modern_geometric": {
        "headings": "font-family: 'Barlow Condensed', 'Arial', sans-serif",
        "subheadings": "font-family: 'PT Sans', 'Arial', sans-serif",
        "body": "font-family: 'Open Sans', 'Helvetica', sans-serif",
        "accent": "font-family: 'Fredoka One', cursive",
        "google_fonts": ["Barlow+Condensed:wght@300;400;500;600;700", "PT+Sans:wght@400;700", "Open+Sans:wght@300;400;600;700", "Fredoka+One"]
    },
    "luxury_artistic": {
        "headings": "font-family: 'Prata', 'Georgia', serif",
        "subheadings": "font-family: 'Crimson Text', 'Times New Roman', serif",
        "body": "font-family: 'Inter', 'Helvetica', sans-serif",
        "accent": "font-family: 'Dancing Script', cursive",
        "google_fonts": ["Prata", "Crimson+Text:wght@400;600", "Inter:wght@300;400;500;600", "Dancing+Script:wght@400;500;600;700"]
    },
    # NEW CURSIVE LUXURY FONT PALETTES
    "elegant_cursive": {
        "headings": "font-family: 'Lobster', cursive",
        "subheadings": "font-family: 'Dancing Script', cursive",
        "body": "font-family: 'Inter', 'Helvetica', sans-serif",
        "accent": "font-family: 'Great Vibes', cursive",
        "google_fonts": ["Lobster", "Dancing+Script:wght@400;500;600;700", "Inter:wght@300;400;500;600", "Great+Vibes"]
    },
    "luxury_script": {
        "headings": "font-family: 'Allura', cursive",
        "subheadings": "font-family: 'Dancing Script', cursive",
        "body": "font-family: 'Lato', 'Helvetica', sans-serif",
        "accent": "font-family: 'Kaushan Script', cursive",
        "google_fonts": ["Allura", "Dancing+Script:wght@400;500;600;700", "Lato:wght@300;400;700", "Kaushan+Script"]
    },
    "sophisticated_cursive": {
        "headings": "font-family: 'Alex Brush', cursive",
        "subheadings": "font-family: 'Great Vibes', cursive",
        "body": "font-family: 'Open Sans', 'Helvetica', sans-serif",
        "accent": "font-family: 'Dancing Script', cursive",
        "google_fonts": ["Alex+Brush", "Great+Vibes", "Open+Sans:wght@300;400;600;700", "Dancing+Script:wght@400;500;600;700"]
    },
    "premium_script": {
        "headings": "font-family: 'Yellowtail', cursive",
        "subheadings": "font-family: 'Kaushan Script', cursive",
        "body": "font-family: 'Source Sans Pro', 'Helvetica', sans-serif",
        "accent": "font-family: 'Allura', cursive",
        "google_fonts": ["Yellowtail", "Kaushan+Script", "Source+Sans+Pro:wght@300;400;600", "Allura"]
    },
    "elegant_handwriting": {
        "headings": "font-family: 'Satisfy', cursive",
        "subheadings": "font-family: 'Dancing Script', cursive",
        "body": "font-family: 'Nunito', 'Arial', sans-serif",
        "accent": "font-family: 'Great Vibes', cursive",
        "google_fonts": ["Satisfy", "Dancing+Script:wght@400;500;600;700", "Nunito:wght@300;400;600;700", "Great+Vibes"]
    },
    "luxury_calligraphy": {
        "headings": "font-family: 'Amatic SC', cursive",
        "subheadings": "font-family: 'Alex Brush', cursive",
        "body": "font-family: 'Lato', 'Helvetica', sans-serif",
        "accent": "font-family: 'Dancing Script', cursive",
        "google_fonts": ["Amatic+SC:wght@400;700", "Alex+Brush", "Lato:wght@300;400;700", "Dancing+Script:wght@400;500;600;700"]
    },
    "stylish_script": {
        "headings": "font-family: 'Pacifico', cursive",
        "subheadings": "font-family: 'Yellowtail', cursive",
        "body": "font-family: 'Inter', 'Helvetica', sans-serif",
        "accent": "font-family: 'Kaushan Script', cursive",
        "google_fonts": ["Pacifico", "Yellowtail", "Inter:wght@300;400;500;600", "Kaushan+Script"]
    },
    "premium_handwriting": {
        "headings": "font-family: 'Righteous', cursive",
        "subheadings": "font-family: 'Satisfy', cursive",
        "body": "font-family: 'Open Sans', 'Helvetica', sans-serif",
        "accent": "font-family: 'Allura', cursive",
        "google_fonts": ["Righteous", "Satisfy", "Open+Sans:wght@300;400;600;700", "Allura"]
    },
    "elegant_signature": {
        "headings": "font-family: 'Great Vibes', cursive",
        "subheadings": "font-family: 'Alex Brush', cursive",
        "body": "font-family: 'Lato', 'Helvetica', sans-serif",
        "accent": "font-family: 'Dancing Script', cursive",
        "google_fonts": ["Great+Vibes", "Alex+Brush", "Lato:wght@300;400;700", "Dancing+Script:wght@400;500;600;700"]
    },
    "luxury_signature": {
        "headings": "font-family: 'Kaushan Script', cursive",
        "subheadings": "font-family: 'Great Vibes', cursive",
        "body": "font-family: 'Source Sans Pro', 'Helvetica', sans-serif",
        "accent": "font-family: 'Yellowtail', cursive",
        "google_fonts": ["Kaushan+Script", "Great+Vibes", "Source+Sans+Pro:wght@300;400;600", "Yellowtail"]
    },
    "sophisticated_signature": {
        "headings": "font-family: 'Allura', cursive",
        "subheadings": "font-family: 'Satisfy', cursive",
        "body": "font-family: 'Inter', 'Helvetica', sans-serif",
        "accent": "font-family: 'Alex Brush', cursive",
        "google_fonts": ["Allura", "Satisfy", "Inter:wght@300;400;500;600", "Alex+Brush"]
    },
    "premium_signature": {
        "headings": "font-family: 'Dancing Script', cursive",
        "subheadings": "font-family: 'Pacifico', cursive",
        "body": "font-family: 'Nunito', 'Arial', sans-serif",
        "accent": "font-family: 'Great Vibes', cursive",
        "google_fonts": ["Dancing+Script:wght@400;500;600;700", "Pacifico", "Nunito:wght@300;400;600;700", "Great+Vibes"]
    }
}

# Enhanced Luxury Color Palettes - Gradient-Based, with Descriptions for Intelligent Selection
LUXURY_COLOR_PALETTES = {
    # GOLD THEMES - GRADIENT BACKGROUNDS
    "gold_mixed_luxury": {
        "primary": "#D4AF37",      # Gold
        "secondary": "#B8860B",    # Dark Goldenrod
        "accent": "#FFD700",       # Bright Gold
        "background": "linear-gradient(135deg, #F4E4BC 0%, #D4AF37 50%, #B8860B 100%)",
        "text_primary": "#2C1810", # Dark Brown
        "text_secondary": "#8B4513", # Saddle Brown
        "gradient": "linear-gradient(135deg, #D4AF37 0%, #FFD700 50%, #B8860B 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F4E4BC 0%, #D4AF37 100%)",
        "gradient_accent": "linear-gradient(90deg, #FFD700 0%, #D4AF37 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F4E4BC 0%, #D4AF37 50%, #B8860B 100%)",
        "description": "A classic and opulent theme with warm, radiant gold gradients and rich, dark brown text for a timeless, elegant feel."
    },
    "champagne_luxury": {
        "primary": "#F7E7CE",      # Champagne
        "secondary": "#DAA520",    # Goldenrod
        "accent": "#FFD700",       # Gold
        "background": "linear-gradient(135deg, #FFF8DC 0%, #F7E7CE 50%, #DAA520 100%)",
        "text_primary": "#8B4513", # Saddle Brown
        "text_secondary": "#A0522D", # Sienna
        "gradient": "linear-gradient(135deg, #F7E7CE 0%, #DAA520 50%, #8B4513 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF8DC 0%, #F7E7CE 100%)",
        "gradient_accent": "linear-gradient(90deg, #DAA520 0%, #F7E7CE 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF8DC 0%, #F7E7CE 50%, #DAA520 100%)",
        "description": "A light, celebratory, and sophisticated palette with soft champagne and golden tones, perfect for high-end, elegant brands."
    },
    
    # EMERALD THEMES - VIBRANT GRADIENTS
    "emerald_mixed_prestige": {
        "primary": "#50C878",      # Emerald Green
        "secondary": "#228B22",    # Forest Green
        "accent": "#00FF7F",       # Spring Green
        "background": "linear-gradient(135deg, #E0F8E0 0%, #50C878 50%, #228B22 100%)",
        "text_primary": "#0F4C0F", # Dark Green
        "text_secondary": "#2E8B57", # Sea Green
        "gradient": "linear-gradient(135deg, #50C878 0%, #00FF7F 50%, #228B22 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E0F8E0 0%, #50C878 100%)",
        "gradient_accent": "linear-gradient(90deg, #00FF7F 0%, #50C878 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E0F8E0 0%, #50C878 50%, #228B22 100%)",
        "description": "A vibrant and prestigious theme with rich emerald greens, suggesting wealth, nature, and growth. Ideal for finance or wellness."
    },
    "forest_luxury": {
        "primary": "#228B22",      # Forest Green
        "secondary": "#006400",    # Dark Green
        "accent": "#32CD32",       # Lime Green
        "background": "linear-gradient(135deg, #F0FFF0 0%, #90EE90 50%, #228B22 100%)",
        "text_primary": "#0A3A0A", # Very Dark Green
        "text_secondary": "#2E8B57", # Sea Green
        "gradient": "linear-gradient(135deg, #228B22 0%, #32CD32 50%, #006400 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F0FFF0 0%, #90EE90 100%)",
        "gradient_accent": "linear-gradient(90deg, #32CD32 0%, #228B22 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F0FFF0 0%, #90EE90 50%, #228B22 100%)",
        "description": "A deep, natural, and calming palette with forest greens, perfect for organic, eco-friendly, or grounded luxury brands."
    },
    
    # PURPLE THEMES - ROYAL GRADIENTS
    "purple_mixed_royal": {
        "primary": "#663399",      # Royal Purple
        "secondary": "#4B0082",    # Indigo
        "accent": "#9370DB",       # Medium Purple
        "background": "linear-gradient(135deg, #E6E6FA 0%, #9370DB 50%, #663399 100%)",
        "text_primary": "#2E1A2E", # Dark Purple
        "text_secondary": "#4B0082", # Indigo
        "gradient": "linear-gradient(135deg, #663399 0%, #9370DB 50%, #4B0082 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E6E6FA 0%, #9370DB 100%)",
        "gradient_accent": "linear-gradient(90deg, #9370DB 0%, #663399 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E6E6FA 0%, #9370DB 50%, #663399 100%)",
        "description": "A royal and creative theme combining deep purples and indigo, suggesting wisdom, luxury, and spirituality."
    },
    "lavender_luxury": {
        "primary": "#E6E6FA",      # Lavender
        "secondary": "#9370DB",    # Medium Purple
        "accent": "#DA70D6",       # Orchid
        "background": "linear-gradient(135deg, #F0E6FF 0%, #E6E6FA 50%, #DA70D6 100%)",
        "text_primary": "#4B0082", # Indigo
        "text_secondary": "#663399", # Royal Purple
        "gradient": "linear-gradient(135deg, #E6E6FA 0%, #DA70D6 50%, #9370DB 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F0E6FF 0%, #E6E6FA 100%)",
        "gradient_accent": "linear-gradient(90deg, #DA70D6 0%, #E6E6FA 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F0E6FF 0%, #E6E6FA 50%, #DA70D6 100%)",
        "description": "A soft, calm, and feminine palette with gentle lavender and orchid gradients, perfect for beauty, wellness, or delicate brands."
    },
    
    # BLUE THEMES - OCEAN GRADIENTS
    "sapphire_mixed_premium": {
        "primary": "#0F52BA",      # Sapphire Blue
        "secondary": "#1E3A8A",    # Dark Blue
        "accent": "#00BFFF",       # Deep Sky Blue
        "background": "linear-gradient(135deg, #E0F2FF 0%, #87CEEB 50%, #0F52BA 100%)",
        "text_primary": "#0A0E27", # Very Dark Blue
        "text_secondary": "#1E3A8A", # Dark Blue
        "gradient": "linear-gradient(135deg, #0F52BA 0%, #00BFFF 50%, #1E3A8A 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E0F2FF 0%, #87CEEB 100%)",
        "gradient_accent": "linear-gradient(90deg, #00BFFF 0%, #0F52BA 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E0F2FF 0%, #87CEEB 50%, #0F52BA 100%)",
        "description": "A corporate, trustworthy, and premium theme with deep sapphire blues, ideal for tech, finance, or professional services."
    },
    "teal_mixed_elegance": {
        "primary": "#008B8B",      # Dark Cyan
        "secondary": "#2F4F4F",    # Dark Slate Gray
        "accent": "#20B2AA",       # Light Sea Green
        "background": "linear-gradient(135deg, #E0FFFF 0%, #AFEEEE 50%, #008B8B 100%)",
        "text_primary": "#0F2B2B", # Very Dark Teal
        "text_secondary": "#2F4F4F", # Dark Slate Gray
        "gradient": "linear-gradient(135deg, #008B8B 0%, #20B2AA 50%, #2F4F4F 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E0FFFF 0%, #AFEEEE 100%)",
        "gradient_accent": "linear-gradient(90deg, #20B2AA 0%, #008B8B 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E0FFFF 0%, #AFEEEE 50%, #008B8B 100%)",
        "description": "A modern, clean, and refreshing palette with elegant teal and cyan gradients. Great for communication, health, or tech startups."
    },
    
    # RED/ORANGE THEMES - WARM GRADIENTS
    "burgundy_mixed_luxury": {
        "primary": "#800020",      # Burgundy
        "secondary": "#8B0000",    # Dark Red
        "accent": "#DC143C",       # Crimson
        "background": "linear-gradient(135deg, #FFE4E1 0%, #F0A0A0 50%, #800020 100%)",
        "text_primary": "#4B0000", # Dark Red
        "text_secondary": "#8B0000", # Dark Red
        "gradient": "linear-gradient(135deg, #800020 0%, #DC143C 50%, #8B0000 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFE4E1 0%, #F0A0A0 100%)",
        "gradient_accent": "linear-gradient(90deg, #DC143C 0%, #800020 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFE4E1 0%, #F0A0A0 50%, #800020 100%)",
        "description": "A bold, passionate, and luxurious theme with deep burgundy and crimson reds. Perfect for high-end, powerful, and confident brands."
    },
    "coral_mixed_elegance": {
        "primary": "#FF7F50",      # Coral
        "secondary": "#CD5C5C",    # Indian Red
        "accent": "#FF6347",       # Tomato
        "background": "linear-gradient(135deg, #FFF8DC 0%, #FFB6C1 50%, #FF7F50 100%)",
        "text_primary": "#8B0000", # Dark Red
        "text_secondary": "#CD5C5C", # Indian Red
        "gradient": "linear-gradient(135deg, #FF7F50 0%, #FF6347 50%, #CD5C5C 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF8DC 0%, #FFB6C1 100%)",
        "gradient_accent": "linear-gradient(90deg, #FF6347 0%, #FF7F50 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF8DC 0%, #FFB6C1 50%, #FF7F50 100%)",
        "description": "A warm, vibrant, and energetic palette with elegant coral and red gradients. Ideal for creative, lively, and modern brands."
    },
    
    # COPPER/BRONZE THEMES - METALLIC GRADIENTS
    "copper_mixed_sophistication": {
        "primary": "#B87333",      # Copper
        "secondary": "#8B4513",    # Saddle Brown
        "accent": "#FF8C00",       # Dark Orange
        "background": "linear-gradient(135deg, #F5DEB3 0%, #DEB887 50%, #B87333 100%)",
        "text_primary": "#2F1B14", # Dark Brown
        "text_secondary": "#8B4513", # Saddle Brown
        "gradient": "linear-gradient(135deg, #B87333 0%, #FF8C00 50%, #8B4513 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F5DEB3 0%, #DEB887 100%)",
        "gradient_accent": "linear-gradient(90deg, #FF8C00 0%, #B87333 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F5DEB3 0%, #DEB887 50%, #B87333 100%)",
        "description": "A sophisticated, warm, and industrial theme with metallic copper gradients and rich brown text. Great for artisanal or premium products."
    },
    "bronze_luxury": {
        "primary": "#CD7F32",      # Bronze
        "secondary": "#8B4513",    # Saddle Brown
        "accent": "#DAA520",       # Goldenrod
        "background": "linear-gradient(135deg, #FFF8DC 0%, #F5DEB3 50%, #CD7F32 100%)",
        "text_primary": "#2F1B14", # Dark Brown
        "text_secondary": "#8B4513", # Saddle Brown
        "gradient": "linear-gradient(135deg, #CD7F32 0%, #DAA520 50%, #8B4513 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF8DC 0%, #F5DEB3 100%)",
        "gradient_accent": "linear-gradient(90deg, #DAA520 0%, #CD7F32 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF8DC 0%, #F5DEB3 50%, #CD7F32 100%)",
        "description": "A classic, earthy, and warm palette with metallic bronze gradients, suggesting durability, quality, and timelessness."
    },
    
    # ROSE/PINK THEMES - ROMANTIC GRADIENTS
    "rose_gold_mixed": {
        "primary": "#E8B4B8",      # Rose Gold
        "secondary": "#CD5C5C",    # Indian Red
        "accent": "#FF69B4",       # Hot Pink
        "background": "linear-gradient(135deg, #FFF0F5 0%, #FFB6C1 50%, #E8B4B8 100%)",
        "text_primary": "#8B0000", # Dark Red
        "text_secondary": "#CD5C5C", # Indian Red
        "gradient": "linear-gradient(135deg, #E8B4B8 0%, #FF69B4 50%, #CD5C5C 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF0F5 0%, #FFB6C1 100%)",
        "gradient_accent": "linear-gradient(90deg, #FF69B4 0%, #E8B4B8 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF0F5 0%, #FFB6C1 50%, #E8B4B8 100%)",
        "description": "A romantic, soft, and feminine palette with trendy rose gold gradients. Perfect for jewelry, beauty, wedding, or lifestyle brands."
    },
    "ivory_luxury": {
        "primary": "#FFFFF0",      # Ivory
        "secondary": "#DAA520",    # Goldenrod
        "accent": "#FFD700",       # Gold
        "background": "linear-gradient(135deg, #FFFEF7 0%, #FFFFF0 50%, #F5DEB3 100%)",
        "text_primary": "#8B4513", # Saddle Brown
        "text_secondary": "#A0522D", # Sienna
        "gradient": "linear-gradient(135deg, #FFFFF0 0%, #FFD700 50%, #DAA520 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFFEF7 0%, #FFFFF0 100%)",
        "gradient_accent": "linear-gradient(90deg, #FFD700 0%, #FFFFF0 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFFEF7 0%, #FFFFF0 50%, #F5DEB3 100%)",
        "description": "A minimal, clean, and elegant palette with soft ivory and gold gradients. Ideal for premium, clean, and sophisticated brands."
    },
    
    # MODERN DARK THEMES - GRADIENT DARK EFFECTS
    "onyx_mixed_premium": {
        "primary": "#708090",      # Slate Gray
        "secondary": "#2F4F4F",    # Dark Slate Gray
        "accent": "#C0C0C0",       # Silver
        "background": "linear-gradient(135deg, #F5F5F5 0%, #D3D3D3 50%, #708090 100%)",
        "text_primary": "#2F2F2F", # Dark Gray
        "text_secondary": "#696969", # Dim Gray
        "gradient": "linear-gradient(135deg, #708090 0%, #C0C0C0 50%, #2F4F4F 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F5F5F5 0%, #D3D3D3 100%)",
        "gradient_accent": "linear-gradient(90deg, #C0C0C0 0%, #708090 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F5F5F5 0%, #D3D3D3 50%, #708090 100%)",
        "description": "A modern, minimalist, and sophisticated dark theme with slate gray and silver tones. Excellent for tech, automotive, or high-end gadgets."
    },
    "midnight_mixed_luxury": {
        "primary": "#4169E1",      # Royal Blue
        "secondary": "#191970",    # Midnight Blue
        "accent": "#87CEEB",       # Sky Blue
        "background": "linear-gradient(135deg, #E6F3FF 0%, #B0C4DE 50%, #4169E1 100%)",
        "text_primary": "#000080", # Navy
        "text_secondary": "#191970", # Midnight Blue
        "gradient": "linear-gradient(135deg, #4169E1 0%, #87CEEB 50%, #191970 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E6F3FF 0%, #B0C4DE 100%)",
        "gradient_accent": "linear-gradient(90deg, #87CEEB 0%, #4169E1 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E6F3FF 0%, #B0C4DE 50%, #4169E1 100%)",
        "description": "A calm, corporate, and trustworthy dark theme with deep midnight and royal blues. Perfect for tech, finance, or business services."
    }
}

def get_luxury_font_palette(palette_name: str = "elegant_serif") -> dict:
    """Get a luxury font palette by name."""
    return LUXURY_FONT_PALETTES.get(palette_name, LUXURY_FONT_PALETTES["elegant_serif"])

def get_luxury_color_palette(palette_name: str = "gold_mixed_luxury") -> dict:
    """Get a luxury color palette by name."""
    return LUXURY_COLOR_PALETTES.get(palette_name, LUXURY_COLOR_PALETTES["gold_mixed_luxury"])

def get_random_luxury_combination() -> tuple:
    """Get a random luxury font and color combination with balanced theme selection."""
    font_palette = random.choice(list(LUXURY_FONT_PALETTES.keys()))
    color_palette = random.choice(list(LUXURY_COLOR_PALETTES.keys()))
    
    return font_palette, color_palette

def get_smart_luxury_combination(user_text: str = "") -> tuple:
    """
    Get a smart luxury font and color combination based on an LLM analysis of the user's prompt.
    """
    if not user_text or not user_text.strip():
        return get_random_luxury_combination()

    # Default to a random choice
    font_palette_name = random.choice(list(LUXURY_FONT_PALETTES.keys()))
    color_palette_name = random.choice(list(LUXURY_COLOR_PALETTES.keys()))

    try:
        # Prepare the list of available palettes for the LLM
        palette_options = ""
        for name, data in LUXURY_COLOR_PALETTES.items():
            palette_options += f"- `{name}`: {data['description']}\n"

        system_prompt = (
            "You are a design expert. Your task is to select the best color palette "
            "from a given list to match the user's design request. "
            "Analyze the user's prompt for theme, mood, and industry. "
            "Respond with ONLY the chosen palette name (e.g., 'gold_mixed_luxury')."
        )
        
        user_prompt = (
            f"Here is the user's design request:\n"
            f"'''\n{user_text}\n'''\n\n"
            f"Here are the available color palettes:\n"
            f"{palette_options}\n\n"
            f"Based on the user's request, which single color palette is the best fit? "
            f"Return ONLY the name of the palette."
        )

        chat_model = get_chat_model(temperature=0.0)
        
        response = chat_model.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        
        chosen_palette = response.content.strip().replace("`", "")

        # Validate the response
        if chosen_palette in LUXURY_COLOR_PALETTES:
            color_palette_name = chosen_palette
            print(f"🧠 LLM selected color palette: {color_palette_name}")
        else:
            print(f"⚠️ LLM returned an invalid palette name ('{chosen_palette}'). Using random selection as a fallback.")
            
    except Exception as e:
        print(f"Error during LLM palette selection: {e}. Using random selection as a fallback.")
        # Fallback to random if the LLM call fails
        return get_random_luxury_combination()

    return font_palette_name, color_palette_name


def generate_luxury_css_variables(color_palette: dict, font_palette: dict) -> str:
    """Generate CSS variables for luxury design with gradient backgrounds."""
    css_vars = [
        ":root {",
        f"  --luxury-primary: {color_palette['primary']};",
        f"  --luxury-secondary: {color_palette['secondary']};", 
        f"  --luxury-accent: {color_palette['accent']};",
        f"  --luxury-background: {color_palette['background']};",
        f"  --luxury-text-primary: {color_palette['text_primary']};",
        f"  --luxury-text-secondary: {color_palette['text_secondary']};",
        f"  --luxury-gradient: {color_palette['gradient']};",
        f"  --luxury-gradient-secondary: {color_palette.get('gradient_secondary', color_palette['gradient'])};",
        f"  --luxury-gradient-accent: {color_palette.get('gradient_accent', color_palette['gradient'])};",
        f"  --luxury-gradient-mixed: {color_palette.get('gradient_mixed', color_palette['gradient'])};",
        f"  --luxury-font-heading: {font_palette['headings']};",
        f"  --luxury-font-subheading: {font_palette['subheadings']};",
        f"  --luxury-font-body: {font_palette['body']};",
        f"  --luxury-font-accent: {font_palette['accent']};",
        "}"
    ]
    return "\n".join(css_vars)

def get_google_fonts_import(font_palette: dict) -> str:
    """Generate Google Fonts import statement."""
    fonts = "&family=".join(font_palette["google_fonts"])
    return f"@import url('https://fonts.googleapis.com/css2?family={fonts}&display=swap');"

def get_font_usage_guide() -> str:
    """Get a guide for using different fonts throughout the design."""
    return """
## 🎨 FONT USAGE GUIDE - 3-FONT SYSTEM

### **FONT HIERARCHY SYSTEM:**
1. **HEADINGS** (H1, H2, H3) - Use heading font for impact and elegance
2. **CONTENT** (Paragraphs, Body Text) - Use body font for readability  
3. **ACCENTS** (CTAs, Special Text) - Use accent font for style and flair

### **APPLICATION RULES:**
- **Main Headlines**: Use heading font with bold weight (600-700)
- **Subheadings**: Use subheading font with medium weight (500-600)
- **Body Text**: Use body font with regular weight (400-500)
- **Call-to-Actions**: Use accent font for elegant buttons and special elements
- **Navigation**: Use heading or subheading font for menu items
- **Captions**: Use body font with lighter weight (300-400)

### **STYLISH COMBINATIONS:**
- **Serif + Sans-Serif**: Classic elegance (Playfair Display + Inter)
- **Modern + Script**: Contemporary style (Montserrat + Dancing Script)
- **Geometric + Handwritten**: Creative flair (Poppins + Allura)
- **Tech + Cursive**: Futuristic luxury (Orbitron + Righteous)
"""