"""Company template styling"""

import re

ROYAL_BLUE = "#4169E1"
WHITE = "#FFFFFF"
COVER_FONT = "Arial, sans-serif"
CONTENT_FONT = "Calibri, sans-serif"
COVER_FONT_SIZE = "24pt"
CONTENT_FONT_SIZE = "18pt"
LINE_SPACING = 1.5

PARTNER_LOGOS = {
    "IIT Kanpur": "assets/logos/iitk-accredian-banner.jpg",
    "IIT Guwahati": "assets/logos/iitg-accredian-banner.jpg",
    "Default": "assets/logos/iitk-accredian-banner.jpg"
}

def get_cover_page_html(title: str, topic: str, partner_institute: str) -> str:
    logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
    
    return f"""
    <div class="cover-page">
        <div class="cover-main">
            <h1 class="cover-title">{title}</h1>
            <h2 class="cover-topic">{topic}</h2>
        </div>
        <div class="cover-footer">
            <img src="{logo_path}" class="partner-banner" alt="{partner_institute}">
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
        }}
    </style>
    """

def get_content_page_styles() -> str:
    return f"""
    <style>
        body {{
            font-family: {CONTENT_FONT};
            font-size: {CONTENT_FONT_SIZE};
            line-height: {LINE_SPACING};
            color: #000000;
            margin: 40px;
        }}
        .question-block {{
            margin: 25px 0;
        }}
        .question-number {{
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .question-text {{
            font-weight: bold;
            text-align: justify;
            margin-bottom: 12px;
        }}
        .answer-text {{
            text-align: justify;
            margin-bottom: 20px;
        }}
        .important {{
            font-weight: bold;
            color: {ROYAL_BLUE};
        }}
        .type-badge {{
            font-size: 12pt;
            font-style: italic;
            color: #666666;
            margin-bottom: 10px;
        }}
    </style>
    """

def format_answer_with_important_words(answer: str, important_words: list) -> str:
    formatted = answer
    important_words_sorted = sorted(important_words, key=len, reverse=True)
    
    for word in important_words_sorted:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        formatted = pattern.sub(f'<span class="important">{word}</span>', formatted)
    
    return formatted
