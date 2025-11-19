"""Company template styling for Accredian study materials"""

# Brand colors
ROYAL_BLUE = "#4169E1"
WHITE = "#FFFFFF"

# Typography
COVER_FONT = "Arial, sans-serif"
CONTENT_FONT = "Calibri, sans-serif"
COVER_FONT_SIZE = "24pt"
CONTENT_FONT_SIZE = "18pt"
LINE_SPACING = 1.5

# Partner institute logos (combined banners with Accredian)
PARTNER_LOGOS = {
    "IIT Kanpur": "assets/logos/iitk-accredian-banner.jpg",
    "IIT Guwahati": "assets/logos/iitg-accredian-banner.jpg",
    "Default": "assets/logos/iitk-accredian-banner.jpg"  # Fallback to IITK
}

def get_cover_page_html(title: str, topic: str, partner_institute: str) -> str:
    """
    Generate cover page HTML with royal blue background and white footer
    
    Args:
        title: Document title (e.g., "Interview Questions")
        topic: Subject topic (e.g., "Machine Learning Fundamentals")
        partner_institute: Selected partner (e.g., "IIT Kanpur")
    
    Returns:
        HTML string for cover page
    """
    
    # Get partner logo path (fallback to default if not found)
    logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
    
    cover_html = f"""
    <div class="cover-page">
        <!-- Main blue area with centered text -->
        <div class="cover-main">
            <h1 class="cover-title">{title}</h1>
            <h2 class="cover-topic">{topic}</h2>
        </div>
        
        <!-- White footer with partner logo -->
        <div class="cover-footer">
            <img src="{logo_path}" class="partner-banner" alt="{partner_institute} Partnership">
        </div>
    </div>
    
    <style>
        .cover-page {{
            height: 100vh;
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }}
        
        .cover-main {{
            flex: 1;
            background: {ROYAL_BLUE};
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: {WHITE};
            font-family: {COVER_FONT};
            text-align: center;
            padding: 40px;
        }}
        
        .cover-title {{
            font-size: {COVER_FONT_SIZE};
            margin: 0 0 20px 0;
            font-weight: normal;
        }}
        
        .cover-topic {{
            font-size: {COVER_FONT_SIZE};
            margin: 20px 0 0 0;
            font-weight: normal;
        }}
        
        .cover-footer {{
            background: {WHITE};
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 120px;
        }}
        
        .partner-banner {{
            max-width: 80%;
            max-height: 80px;
            height: auto;
            object-fit: contain;
        }}
    </style>
    """
    
    return cover_html


def get_content_page_styles() -> str:
    """
    Generate CSS styles for content pages
    
    Returns:
        CSS string for content pages styling
    """
    
    styles = f"""
    <style>
        /* Content pages styling */
        body {{
            font-family: {CONTENT_FONT};
            font-size: {CONTENT_FONT_SIZE};
            line-height: {LINE_SPACING};
            color: #000000;
            margin: 40px;
        }}
        
        .content-page {{
            page-break-inside: avoid;
            margin-bottom: 30px;
        }}
        
        .question-block {{
            margin: 25px 0;
            page-break-inside: avoid;
        }}
        
        .question-number {{
            font-size: 16pt;
            font-weight: bold;
            color: #333333;
            margin-bottom: 8px;
        }}
        
        .question-text {{
            font-weight: bold;
            text-align: justify;
            margin-bottom: 12px;
            color: #000000;
        }}
        
        .answer-text {{
            text-align: justify;
            margin-bottom: 20px;
            color: #000000;
        }}
        
        /* Important words styling - bold + royal blue */
        .important {{
            font-weight: bold;
            color: {ROYAL_BLUE};
        }}
        
        /* Type badge styling */
        .type-badge {{
            font-size: 12pt;
            font-style: italic;
            color: #666666;
            margin-bottom: 10px;
        }}
        
        /* Page break control */
        @media print {{
            .question-block {{
                page-break-inside: avoid;
            }}
        }}
    </style>
    """
    
    return styles


def format_answer_with_important_words(answer: str, important_words: list) -> str:
    """
    Format answer text with important words highlighted
    
    Args:
        answer: Answer text
        important_words: List of important words/phrases to highlight
    
    Returns:
        HTML formatted answer with <span class="important"> tags
    """
    
    formatted = answer
    
    # Sort by length (longest first) to avoid partial replacements
    important_words_sorted = sorted(important_words, key=len, reverse=True)
    
    for word in important_words_sorted:
        # Case-insensitive replacement, preserve original case
        import re
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        formatted = pattern.sub(f'<span class="important">{word}</span>', formatted)
    
    return formatted
