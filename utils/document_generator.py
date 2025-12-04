"""Document generators - Logos scaled to 50% of original size"""

from io import BytesIO
from typing import List, Dict
import os

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except:
    WEASYPRINT_AVAILABLE = False

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from utils.company_template import PARTNER_LOGO_URLS, PARTNER_LOGOS

def get_cover_page_html(title: str, topic: str, partner_institute: str) -> str:
    logo_url = PARTNER_LOGO_URLS.get(partner_institute, PARTNER_LOGO_URLS["Default"])
    return f"""
    <div class="cover-page">
        <div class="cover-main">
            <div class="cover-content">
                <h1 class="cover-title">{title}</h1>
                <h2 class="cover-topic">{topic}</h2>
            </div>
        </div>
        <div class="cover-footer">
            <div class="footer-logo-wrapper">
                <img src="{logo_url}" class="partner-banner" alt="{partner_institute}">
            </div>
        </div>
    </div>
    """

class PDFGenerator:
    def __init__(self, title: str, topic: str, partner_institute: str = "IIT Kanpur"):
        self.title = title
        self.topic = topic
        self.partner_institute = partner_institute
    
    def generate(self, qa_pairs: List[Dict]) -> bytes:
        if not WEASYPRINT_AVAILABLE:
            raise Exception("WeasyPrint not available")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page cover {{
            size: A4;
            margin: 0;
        }}
        
        @page content {{
            size: A4;
            margin: 18.3mm 18.3mm 18.3mm 18.3mm;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: Calibri, sans-serif;
            font-size: 14pt;
            line-height: 1.5;
            color: #000000;
        }}
        
        /* COVER PAGE */
        .cover-page {{
            page: cover;
            height: 297mm;
            width: 210mm;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            page-break-after: always;
        }}
        
        .cover-main {{
            background-color: #3030ff;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 87%;
            height: 87%;
            padding: 0;
        }}
        .cover-content {{
            width: 100%;
            height: 100%;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 0;
        }}
        .cover-title {{
            font-size: 27pt;
            font-weight: bold;
            color: #FFFFFF;
            font-family: Calibri, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.2;
        }}
        
        .cover-topic {{
            font-size: 27pt;
            font-weight: normal;
            color: #FFFFFF;
            font-family: Calibri, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.2;
        }}
        .cover-footer {{
            height: 13%;
            background: #FFF;
            width: 100%;
            min-height: 100px;
            display: flex;
            justify-content: center;
            align-items: flex-end;
            position: relative;
            text-align: center;
            padding: 10px 0;
            margin: 0;
        }}
        .footer-logo-wrapper {{
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .partner-banner {{
            /* Scale the logo to 50% of its natural size */
            zoom: 0.5; 
            max-width: 100%;
            height: auto;
            width: auto;
            display: block;
            margin: 0 auto;
            padding: 0;
        }}

        /* CONTENT PAGES */
        .
