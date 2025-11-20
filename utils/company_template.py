"""Company template styling with logo URL"""

import re

ROYAL_BLUE = "#3030ff"
WHITE = "#FFFFFF"
COVER_FONT = "Arial, sans-serif"
CONTENT_FONT = "Calibri, sans-serif"
COVER_FONT_SIZE = "18pt"
CONTENT_FONT_SIZE = "18pt"
LINE_SPACING = 1.5

# Logo URLs (using raw GitHub URLs)
PARTNER_LOGO_URLS = {
    "IIT Kanpur": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitk-accredian-banner.jpg%20.png",
    "IIT Guwahati": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitg-accredian-banner.jpg",
    "Default": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitk-accredian-banner.jpg%20.png"
}

# Local paths (for Word documents)
PARTNER_LOGOS = {
    "IIT Kanpur": "assets/logos/iitk-accredian-banner.jpg .png",
    "IIT Guwahati": "assets/logos/iitg-accredian-banner.jpg",
    "Default": "assets/logos/iitk-accredian-banner.jpg .png"
}

def get_cover_page_html(title: str, topic: str, partner_institute: str) -> str:
    logo_url = PARTNER_LOGO_URLS.get(partner_institute, PARTNER_LOGO_URLS["Default"])
    
    return f"""
    <div class="cover-page">
        <div class="cover-main">
            <h1 class="cover-title">{title}</h1>
            <h2 class="cover-topic">{topic}</h2>
        </div>
        <div class="cover-footer">
            <img src="{logo_url}" class="partner-banner" alt="{partner_institute}" crossorigin="anonymous">
        </div>
    </div>
    <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        .cover-page {{
            height: 297mm;
            width: 210mm;
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }}
        .cover-main {{
            flex: 1;
            background-color: {ROYAL_BLUE} !important;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: {WHITE} !important;
            font-family: {COVER_FONT};
            text-align: center;
            padding: 80px 40px;
        }}
        .cover-title {{
            font-size: {COVER_FONT_SIZE} !important;
            margin: 0 0 40px 0 !important;
            font-weight: bold;
            color: {WHITE} !important;
            line-height: 1.4;
        }}
        .cover-topic {{
            font-size: {COVER_FONT_SIZE} !important;
            margin: 40px 0 0 0 !important;
            font-weight: bold;
            color: {WHITE} !important;
            line-height: 1.4;
        }}
        .cover-footer {{
            background-color: {WHITE} !important;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 160px;
        }}
        .partner-banner {{
            max-width: 80%;
            max-height: 100px;
            height: auto;
            object-fit: contain;
        }}
    </style>
    """

def get_content_page_styles() -> str:
    return f"""
    <style>
        @page {{
            size: A4;
            margin: 30mm 25mm 30mm 25mm;
        }}
        body {{
            font-family: {CONTENT_FONT} !important;
            font-size: {CONTENT_FONT_SIZE} !important;
            line-height: {LINE_SPACING};
            color: #000000;
            margin: 0;
            padding: 0;
        }}
        .content-page {{
            padding: 0;
        }}
        .question-block {{
            margin: 35px 0;
            page-break-inside: avoid;
        }}
        .question-number {{
            font-size: {CONTENT_FONT_SIZE} !important;
            font-weight: bold;
            color: #333333;
            margin-bottom: 12px;
            font-family: {CONTENT_FONT} !important;
        }}
        .question-text {{
            font-weight: bold;
            text-align: justify;
            margin-bottom: 12px;
            color: #000000;
            font-size: {CONTENT_FONT_SIZE} !important;
            font-family: {CONTENT_FONT} !important;
            line-height: {LINE_SPACING};
        }}
        .answer-text {{
            text-align: justify;
            margin-bottom: 20px;
            color: #000000;
            font-size: {CONTENT_FONT_SIZE} !important;
            font-family: {CONTENT_FONT} !important;
            line-height: {LINE_SPACING};
        }}
        .important {{
            font-weight: bold !important;
            color: {ROYAL_BLUE} !important;
        }}
        .type-badge {{
            font-size: 14pt !important;
            font-style: italic;
            color: #666666;
            margin-bottom: 10px;
            font-family: {CONTENT_FONT} !important;
        }}
    </style>
    """

def format_answer_with_important_words(answer: str, important_words: list) -> str:
    if not important_words:
        return answer
    
    formatted = answer
    important_words_sorted = sorted(important_words, key=len, reverse=True)
    
    for word in important_words_sorted:
        if not word or not isinstance(word, str):
            continue
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        formatted = pattern.sub(f'<span class="important">{word}</span>', formatted)
    
    return formatted
