"""Document generation with company template - PDF and Word formats"""

from io import BytesIO
from datetime import datetime
from typing import List, Dict
import os

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

from utils.company_template import (
    get_cover_page_html,
    get_content_page_styles,
    format_answer_with_important_words,
    ROYAL_BLUE
)
from utils.important_words_detector import ImportantWordsDetector


class PDFGenerator:
    """Generate PDF with company template using WeasyPrint"""
    
    def __init__(self, title: str, topic: str, partner_institute: str = "IIT Kanpur"):
        """
        Initialize PDF generator with company branding
        
        Args:
            title: Document title (e.g., "Interview Questions")
            topic: Subject topic
            partner_institute: Partner institution name
        """
        self.title = title
        self.topic = topic
        self.partner_institute = partner_institute
        self.detector = ImportantWordsDetector(use_ai=False)
    
    def generate(self, qa_pairs: List[Dict]) -> bytes:
        """
        Generate PDF with company template
        
        Args:
            qa_pairs: List of question-answer dictionaries
        
        Returns:
            PDF file as bytes
        """
        if not WEASYPRINT_AVAILABLE:
            raise Exception("WeasyPrint not available. Install with: pip install weasyprint")
        
        # Detect important words for all answers
        important_words_map = self.detector.detect_batch(qa_pairs)
        
        # Build HTML document
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {get_content_page_styles()}
        </head>
        <body>
            {get_cover_page_html(self.title, self.topic, self.partner_institute)}
            
            <div class="content-page">
        """
        
        # Add questions and answers
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            qa_id = qa.get('id')
            
            # Format answer with important words highlighted
            important_words = important_words_map.get(qa_id, [])
            formatted_answer = format_answer_with_important_words(answer, important_words)
            
            html_content += f"""
            <div class="question-block">
                <div class="question-number">Question {i}</div>
                <div class="question-text">{question}</div>
                <div class="type-badge">[{qa_type}]</div>
                <div class="answer-text">{formatted_answer}</div>
            </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes


class WordDocumentGenerator:
    """Generate Word document with company template"""
    
    def __init__(self):
        """Initialize Word document generator"""
        self.detector = ImportantWordsDetector(use_ai=False)
    
    def _add_cover_page(self, doc: Document, title: str, topic: str, partner_institute: str):
        """
        Add cover page with title, topic, and logo
        
        Args:
            doc: Document object
            title: Document title
            topic: Subject topic
            partner_institute: Partner institution
        """
        # Add spacing
        for _ in range(5):
            doc.add_paragraph()
        
        # Title
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.name = 'Arial'
        title_run.font.size = Pt(24)
        title_run.font.color.rgb = RGBColor(65, 105, 225)
        title_run.bold = True
        
        doc.add_paragraph()
        
        # Topic
        topic_para = doc.add_paragraph()
        topic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        topic_run = topic_para.add_run(topic)
        topic_run.font.name = 'Arial'
        topic_run.font.size = Pt(24)
        topic_run.font.color.rgb = RGBColor(65, 105, 225)
        topic_run.bold = True
        
        # Add spacing before logo
        for _ in range(8):
            doc.add_paragraph()
        
        # Add partner logo if exists
        from utils.company_template import PARTNER_LOGOS
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS.get("Default"))
        
        if os.path.exists(logo_path):
            logo_para = doc.add_paragraph()
            logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = logo_para.add_run()
            run.add_picture(logo_path, width=Inches(5))
        
        # Page break after cover
        doc.add_page_break()
    
    def _apply_answer_formatting(self, paragraph, answer: str, important_words: List[str]):
        """
        Apply formatting to answer with important words highlighted
        
        Args:
            paragraph: Paragraph object
            answer: Answer text
            important_words: List of words to highlight
        """
        # Split answer by important words and format
        remaining = answer
        
        for word in important_words:
            if word.lower() in remaining.lower():
                import re
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                match = pattern.search(remaining)
                
                if match:
                    # Text before important word
                    before = remaining[:match.start()]
                    if before:
                        run = paragraph.add_run(before)
                        run.font.name = 'Calibri'
                        run.font.size = Pt(18)
                    
                    # Important word (bold + blue)
                    important_run = paragraph.add_run(match.group())
                    important_run.font.name = 'Calibri'
                    important_run.font.size = Pt(18)
                    important_run.font.bold = True
                    important_run.font.color.rgb = RGBColor(65, 105, 225)
                    
                    # Continue with rest
                    remaining = remaining[match.end():]
        
        # Add remaining text
        if remaining:
            run = paragraph.add_run(remaining)
            run.font.name = 'Calibri'
            run.font.size = Pt(18)
    
    def generate(self, qa_pairs: List[Dict], title: str, topic: str, partner_institute: str = "IIT Kanpur") -> bytes:
        """
        Generate Word document with company template
        
        Args:
            qa_pairs: List of Q&A dictionaries
            title: Document title
            topic: Subject topic
            partner_institute: Partner institution
        
        Returns:
            Word document as bytes
        """
        doc = Document()
        
        # Add cover page
        self._add_cover_page(doc, title, topic, partner_institute)
        
        # Detect important words
        important_words_map = self.detector.detect_batch(qa_pairs)
        
        # Add questions and answers
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            qa_id = qa.get('id')
            
            # Question number
            q_num_para = doc.add_paragraph()
            q_num_run = q_num_para.add_run(f"Question {i}")
            q_num_run.font.name = 'Calibri'
            q_num_run.font.size = Pt(16)
            q_num_run.font.bold = True
            
            # Question text
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(question)
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(18)
            q_run.font.bold = True
            q_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            
            # Type badge
            type_para = doc.add_paragraph()
            type_run = type_para.add_run(f"[{qa_type}]")
            type_run.font.name = 'Calibri'
            type_run.font.size = Pt(12)
            type_run.font.italic = True
            
            # Answer with important words highlighted
            a_para = doc.add_paragraph()
            a_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            a_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            
            important_words = important_words_map.get(qa_id, [])
            self._apply_answer_formatting(a_para, answer, important_words)
            
            # Spacing
            doc.add_paragraph()
        
        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
