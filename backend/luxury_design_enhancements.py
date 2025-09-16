"""
Luxury Design Enhancement System
This module provides luxury fonts and colors to enhance UI generation
while keeping the JSON schema structure intact.
"""

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

# Enhanced Luxury Color Palettes - Gradient-Based, No Solid Dark Colors
LUXURY_COLOR_PALETTES = {
    # GOLD THEMES - GRADIENT BACKGROUNDS
    "gold_mixed_luxury": {
        "primary": "#D4AF37",      # Gold
        "secondary": "#B8860B",    # Dark Goldenrod
        "accent": "#FFD700",       # Bright Gold
        "background": "linear-gradient(135deg, #F4E4BC 0%, #D4AF37 50%, #B8860B 100%)",  # Gradient instead of solid
        "text_primary": "#2C1810", # Dark Brown (contrasts with light gradient)
        "text_secondary": "#8B4513", # Saddle Brown
        "gradient": "linear-gradient(135deg, #D4AF37 0%, #FFD700 50%, #B8860B 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F4E4BC 0%, #D4AF37 100%)",
        "gradient_accent": "linear-gradient(90deg, #FFD700 0%, #D4AF37 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F4E4BC 0%, #D4AF37 50%, #B8860B 100%)",
        "description": "Gold luxury with warm gradient backgrounds and rich text colors"
    },
    "champagne_luxury": {
        "primary": "#F7E7CE",      # Champagne
        "secondary": "#DAA520",    # Goldenrod
        "accent": "#FFD700",       # Gold
        "background": "linear-gradient(135deg, #FFF8DC 0%, #F7E7CE 50%, #DAA520 100%)",  # Light gradient
        "text_primary": "#8B4513", # Saddle Brown
        "text_secondary": "#A0522D", # Sienna
        "gradient": "linear-gradient(135deg, #F7E7CE 0%, #DAA520 50%, #8B4513 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF8DC 0%, #F7E7CE 100%)",
        "gradient_accent": "linear-gradient(90deg, #DAA520 0%, #F7E7CE 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF8DC 0%, #F7E7CE 50%, #DAA520 100%)",
        "description": "Champagne luxury with warm light gradients and rich brown text"
    },
    
    # EMERALD THEMES - VIBRANT GRADIENTS
    "emerald_mixed_prestige": {
        "primary": "#50C878",      # Emerald Green
        "secondary": "#228B22",    # Forest Green
        "accent": "#00FF7F",       # Spring Green
        "background": "linear-gradient(135deg, #E0F8E0 0%, #50C878 50%, #228B22 100%)",  # Green gradient
        "text_primary": "#0F4C0F", # Dark Green
        "text_secondary": "#2E8B57", # Sea Green
        "gradient": "linear-gradient(135deg, #50C878 0%, #00FF7F 50%, #228B22 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E0F8E0 0%, #50C878 100%)",
        "gradient_accent": "linear-gradient(90deg, #00FF7F 0%, #50C878 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E0F8E0 0%, #50C878 50%, #228B22 100%)",
        "description": "Emerald prestige with vibrant green gradients and deep green text"
    },
    "forest_luxury": {
        "primary": "#228B22",      # Forest Green
        "secondary": "#006400",    # Dark Green
        "accent": "#32CD32",       # Lime Green
        "background": "linear-gradient(135deg, #F0FFF0 0%, #90EE90 50%, #228B22 100%)",  # Light to dark green
        "text_primary": "#0A3A0A", # Very Dark Green
        "text_secondary": "#2E8B57", # Sea Green
        "gradient": "linear-gradient(135deg, #228B22 0%, #32CD32 50%, #006400 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F0FFF0 0%, #90EE90 100%)",
        "gradient_accent": "linear-gradient(90deg, #32CD32 0%, #228B22 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F0FFF0 0%, #90EE90 50%, #228B22 100%)",
        "description": "Forest luxury with natural green gradients and deep forest text"
    },
    
    # PURPLE THEMES - ROYAL GRADIENTS
    "purple_mixed_royal": {
        "primary": "#663399",      # Royal Purple
        "secondary": "#4B0082",    # Indigo
        "accent": "#9370DB",       # Medium Purple
        "background": "linear-gradient(135deg, #E6E6FA 0%, #9370DB 50%, #663399 100%)",  # Purple gradient
        "text_primary": "#2E1A2E", # Dark Purple
        "text_secondary": "#4B0082", # Indigo
        "gradient": "linear-gradient(135deg, #663399 0%, #9370DB 50%, #4B0082 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E6E6FA 0%, #9370DB 100%)",
        "gradient_accent": "linear-gradient(90deg, #9370DB 0%, #663399 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E6E6FA 0%, #9370DB 50%, #663399 100%)",
        "description": "Royal purple with elegant gradients and deep purple text"
    },
    "lavender_luxury": {
        "primary": "#E6E6FA",      # Lavender
        "secondary": "#9370DB",    # Medium Purple
        "accent": "#DA70D6",       # Orchid
        "background": "linear-gradient(135deg, #F0E6FF 0%, #E6E6FA 50%, #DA70D6 100%)",  # Light purple gradient
        "text_primary": "#4B0082", # Indigo
        "text_secondary": "#663399", # Royal Purple
        "gradient": "linear-gradient(135deg, #E6E6FA 0%, #DA70D6 50%, #9370DB 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F0E6FF 0%, #E6E6FA 100%)",
        "gradient_accent": "linear-gradient(90deg, #DA70D6 0%, #E6E6FA 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F0E6FF 0%, #E6E6FA 50%, #DA70D6 100%)",
        "description": "Lavender luxury with soft purple gradients and rich purple text"
    },
    
    # BLUE THEMES - OCEAN GRADIENTS
    "sapphire_mixed_premium": {
        "primary": "#0F52BA",      # Sapphire Blue
        "secondary": "#1E3A8A",    # Dark Blue
        "accent": "#00BFFF",       # Deep Sky Blue
        "background": "linear-gradient(135deg, #E0F2FF 0%, #87CEEB 50%, #0F52BA 100%)",  # Blue gradient
        "text_primary": "#0A0E27", # Very Dark Blue
        "text_secondary": "#1E3A8A", # Dark Blue
        "gradient": "linear-gradient(135deg, #0F52BA 0%, #00BFFF 50%, #1E3A8A 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E0F2FF 0%, #87CEEB 100%)",
        "gradient_accent": "linear-gradient(90deg, #00BFFF 0%, #0F52BA 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E0F2FF 0%, #87CEEB 50%, #0F52BA 100%)",
        "description": "Sapphire premium with ocean blue gradients and deep blue text"
    },
    "teal_mixed_elegance": {
        "primary": "#008B8B",      # Dark Cyan
        "secondary": "#2F4F4F",    # Dark Slate Gray
        "accent": "#20B2AA",       # Light Sea Green
        "background": "linear-gradient(135deg, #E0FFFF 0%, #AFEEEE 50%, #008B8B 100%)",  # Teal gradient
        "text_primary": "#0F2B2B", # Very Dark Teal
        "text_secondary": "#2F4F4F", # Dark Slate Gray
        "gradient": "linear-gradient(135deg, #008B8B 0%, #20B2AA 50%, #2F4F4F 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E0FFFF 0%, #AFEEEE 100%)",
        "gradient_accent": "linear-gradient(90deg, #20B2AA 0%, #008B8B 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E0FFFF 0%, #AFEEEE 50%, #008B8B 100%)",
        "description": "Teal elegance with refreshing gradients and deep teal text"
    },
    
    # RED/ORANGE THEMES - WARM GRADIENTS
    "burgundy_mixed_luxury": {
        "primary": "#800020",      # Burgundy
        "secondary": "#8B0000",    # Dark Red
        "accent": "#DC143C",       # Crimson
        "background": "linear-gradient(135deg, #FFE4E1 0%, #F0A0A0 50%, #800020 100%)",  # Red gradient
        "text_primary": "#4B0000", # Dark Red
        "text_secondary": "#8B0000", # Dark Red
        "gradient": "linear-gradient(135deg, #800020 0%, #DC143C 50%, #8B0000 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFE4E1 0%, #F0A0A0 100%)",
        "gradient_accent": "linear-gradient(90deg, #DC143C 0%, #800020 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFE4E1 0%, #F0A0A0 50%, #800020 100%)",
        "description": "Burgundy luxury with warm red gradients and deep red text"
    },
    "coral_mixed_elegance": {
        "primary": "#FF7F50",      # Coral
        "secondary": "#CD5C5C",    # Indian Red
        "accent": "#FF6347",       # Tomato
        "background": "linear-gradient(135deg, #FFF8DC 0%, #FFB6C1 50%, #FF7F50 100%)",  # Coral gradient
        "text_primary": "#8B0000", # Dark Red
        "text_secondary": "#CD5C5C", # Indian Red
        "gradient": "linear-gradient(135deg, #FF7F50 0%, #FF6347 50%, #CD5C5C 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF8DC 0%, #FFB6C1 100%)",
        "gradient_accent": "linear-gradient(90deg, #FF6347 0%, #FF7F50 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF8DC 0%, #FFB6C1 50%, #FF7F50 100%)",
        "description": "Coral elegance with warm coral gradients and rich red text"
    },
    
    # COPPER/BRONZE THEMES - METALLIC GRADIENTS
    "copper_mixed_sophistication": {
        "primary": "#B87333",      # Copper
        "secondary": "#8B4513",    # Saddle Brown
        "accent": "#FF8C00",       # Dark Orange
        "background": "linear-gradient(135deg, #F5DEB3 0%, #DEB887 50%, #B87333 100%)",  # Copper gradient
        "text_primary": "#2F1B14", # Dark Brown
        "text_secondary": "#8B4513", # Saddle Brown
        "gradient": "linear-gradient(135deg, #B87333 0%, #FF8C00 50%, #8B4513 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F5DEB3 0%, #DEB887 100%)",
        "gradient_accent": "linear-gradient(90deg, #FF8C00 0%, #B87333 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F5DEB3 0%, #DEB887 50%, #B87333 100%)",
        "description": "Copper sophistication with metallic gradients and rich brown text"
    },
    "bronze_luxury": {
        "primary": "#CD7F32",      # Bronze
        "secondary": "#8B4513",    # Saddle Brown
        "accent": "#DAA520",       # Goldenrod
        "background": "linear-gradient(135deg, #FFF8DC 0%, #F5DEB3 50%, #CD7F32 100%)",  # Bronze gradient
        "text_primary": "#2F1B14", # Dark Brown
        "text_secondary": "#8B4513", # Saddle Brown
        "gradient": "linear-gradient(135deg, #CD7F32 0%, #DAA520 50%, #8B4513 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF8DC 0%, #F5DEB3 100%)",
        "gradient_accent": "linear-gradient(90deg, #DAA520 0%, #CD7F32 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF8DC 0%, #F5DEB3 50%, #CD7F32 100%)",
        "description": "Bronze luxury with warm metallic gradients and rich brown text"
    },
    
    # ROSE/PINK THEMES - ROMANTIC GRADIENTS
    "rose_gold_mixed": {
        "primary": "#E8B4B8",      # Rose Gold
        "secondary": "#CD5C5C",    # Indian Red
        "accent": "#FF69B4",       # Hot Pink
        "background": "linear-gradient(135deg, #FFF0F5 0%, #FFB6C1 50%, #E8B4B8 100%)",  # Rose gradient
        "text_primary": "#8B0000", # Dark Red
        "text_secondary": "#CD5C5C", # Indian Red
        "gradient": "linear-gradient(135deg, #E8B4B8 0%, #FF69B4 50%, #CD5C5C 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFF0F5 0%, #FFB6C1 100%)",
        "gradient_accent": "linear-gradient(90deg, #FF69B4 0%, #E8B4B8 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFF0F5 0%, #FFB6C1 50%, #E8B4B8 100%)",
        "description": "Rose gold with romantic gradients and deep red text"
    },
    "ivory_luxury": {
        "primary": "#FFFFF0",      # Ivory
        "secondary": "#DAA520",    # Goldenrod
        "accent": "#FFD700",       # Gold
        "background": "linear-gradient(135deg, #FFFEF7 0%, #FFFFF0 50%, #F5DEB3 100%)",  # Ivory gradient
        "text_primary": "#8B4513", # Saddle Brown
        "text_secondary": "#A0522D", # Sienna
        "gradient": "linear-gradient(135deg, #FFFFF0 0%, #FFD700 50%, #DAA520 100%)",
        "gradient_secondary": "linear-gradient(45deg, #FFFEF7 0%, #FFFFF0 100%)",
        "gradient_accent": "linear-gradient(90deg, #FFD700 0%, #FFFFF0 100%)",
        "gradient_mixed": "linear-gradient(180deg, #FFFEF7 0%, #FFFFF0 50%, #F5DEB3 100%)",
        "description": "Ivory luxury with soft gradients and rich brown text"
    },
    
    # MODERN DARK THEMES - GRADIENT DARK EFFECTS
    "onyx_mixed_premium": {
        "primary": "#708090",      # Slate Gray
        "secondary": "#2F4F4F",    # Dark Slate Gray
        "accent": "#C0C0C0",       # Silver
        "background": "linear-gradient(135deg, #F5F5F5 0%, #D3D3D3 50%, #708090 100%)",  # Gray gradient
        "text_primary": "#2F2F2F", # Dark Gray
        "text_secondary": "#696969", # Dim Gray
        "gradient": "linear-gradient(135deg, #708090 0%, #C0C0C0 50%, #2F4F4F 100%)",
        "gradient_secondary": "linear-gradient(45deg, #F5F5F5 0%, #D3D3D3 100%)",
        "gradient_accent": "linear-gradient(90deg, #C0C0C0 0%, #708090 100%)",
        "gradient_mixed": "linear-gradient(180deg, #F5F5F5 0%, #D3D3D3 50%, #708090 100%)",
        "description": "Onyx premium with sophisticated gray gradients and dark gray text"
    },
    "midnight_mixed_luxury": {
        "primary": "#4169E1",      # Royal Blue
        "secondary": "#191970",    # Midnight Blue
        "accent": "#87CEEB",       # Sky Blue
        "background": "linear-gradient(135deg, #E6F3FF 0%, #B0C4DE 50%, #4169E1 100%)",  # Blue gradient
        "text_primary": "#000080", # Navy
        "text_secondary": "#191970", # Midnight Blue
        "gradient": "linear-gradient(135deg, #4169E1 0%, #87CEEB 50%, #191970 100%)",
        "gradient_secondary": "linear-gradient(45deg, #E6F3FF 0%, #B0C4DE 100%)",
        "gradient_accent": "linear-gradient(90deg, #87CEEB 0%, #4169E1 100%)",
        "gradient_mixed": "linear-gradient(180deg, #E6F3FF 0%, #B0C4DE 50%, #4169E1 100%)",
        "description": "Midnight luxury with deep blue gradients and navy text"
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
    import random
    
    # Get random font palette
    font_palette = random.choice(list(LUXURY_FONT_PALETTES.keys()))
    
    # Use the new mixed color palettes
    color_palettes = [
        "gold_mixed_luxury", "emerald_mixed_prestige", "purple_mixed_royal",
        "rose_gold_mixed", "sapphire_mixed_premium", "copper_mixed_sophistication",
        "teal_mixed_elegance", "burgundy_mixed_luxury", "forest_mixed_prestige",
        "coral_mixed_elegance", "onyx_mixed_premium", "midnight_mixed_luxury"
    ]
    
    color_palette = random.choice(color_palettes)
    
    return font_palette, color_palette

def get_smart_luxury_combination(user_text: str = "") -> tuple:
    """Get a smart luxury font and color combination based on user preferences."""
    import random
    
    # If no user text, use balanced random selection
    if not user_text or not user_text.strip():
        return get_random_luxury_combination()
    
    user_text_lower = user_text.lower()
    
    # Dark theme keywords
    dark_keywords = ["dark", "black", "midnight", "charcoal", "onyx", "burgundy", "emerald dark", "sapphire dark"]
    
    # Light theme keywords  
    light_keywords = ["light", "white", "bright", "clean", "minimal", "elegant", "champagne", "ivory"]
    
    # Check for dark theme preference
    if any(keyword in user_text_lower for keyword in dark_keywords):
        dark_themes = [
            "onyx_mixed_premium", "midnight_mixed_luxury", "burgundy_mixed_luxury",
            "emerald_mixed_prestige", "purple_mixed_royal", "sapphire_mixed_premium"
        ]
        color_palette = random.choice(dark_themes)
    
    # Check for light theme preference
    elif any(keyword in user_text_lower for keyword in light_keywords):
        light_themes = [
            "gold_mixed_luxury", "rose_gold_mixed", "coral_mixed_elegance",
            "teal_mixed_elegance", "forest_mixed_prestige", "copper_mixed_sophistication"
        ]
        color_palette = random.choice(light_themes)
    
    # For anything else, use balanced random selection
    else:
        return get_random_luxury_combination()
    
    # Get random font palette
    font_palette = random.choice(list(LUXURY_FONT_PALETTES.keys()))
    
    return font_palette, color_palette

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
    fonts = "|".join(font_palette["google_fonts"])
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
