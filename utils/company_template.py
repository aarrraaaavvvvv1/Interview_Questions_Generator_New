"""Company template matching sample document format"""

import re

ROYAL_BLUE = "#3030ff"
WHITE = "#FFFFFF"

# Logo URLs
PARTNER_LOGO_URLS = {
    "IIT Kanpur": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitk-accredian-banner.jpg%20.png",
    "IIT Guwahati": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitg-accredian-banner.jpg",
    "Default": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitk-accredian-banner.jpg%20.png"
}

# Local paths (for Word)
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
            <img src="{logo_url}" class="partner-banner" alt="{partner_institute}">
        </div>
    </div>
    <style>
        @page {{
            size: A4;
            margin: 0;
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
            background-color: {ROYAL_BLUE};
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: {WHITE};
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 80px 40px;
        }}
        .cover-title {{
            font-size: 18pt;
            margin: 0 0 40px 0;
            font-weight: bold;
            color: {WHITE};
        }}
        .cover-topic {{
            font-size: 18pt;
            margin: 40px 0 0 0;
            font-weight: bold;
            color: {WHITE};
        }}
        .cover-footer {{
            background-color: {WHITE};
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
        }}
    </style>
    """

def get_content_page_styles() -> str:
    return """
    <style>
        @page {
            size: A4;
            margin: 25mm;
        }
        body {
            font-family: Calibri, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #000000;
        }
        .question-block {
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        .question-header {
            font-size: 11pt;
            font-weight: bold;
            margin-bottom: 8px;
            color: #000000;
        }
        .answer-header {
            font-size: 11pt;
            font-weight: bold;
            margin-bottom: 8px;
            color: #000000;
        }
        .answer-text {
            font-size: 11pt;
            text-align: justify;
            line-height: 1.5;
            margin-bottom: 15px;
            color: #000000;
        }
    </style>
    """
