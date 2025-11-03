from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from typing import Dict
from datetime import datetime
import os
import re

class PDFGenerator:
    """Generates perfectly formatted PDF documents with proper text alignment and containment"""
    
    def __init__(self):
        self.page_size = letter
        self.styles = getSampleStyleSheet()
        self.page_width, self.page_height = letter
        self.margin = 0.6*inch  # Reduced margin
        self.usable_width = self.page_width - (2 * self.margin)
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom styles with proper text containment"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=20,
            spaceBefore=10,
            alignment=1,  # Center
            splitLongWords=True,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuestionNumber',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=8,
            spaceBefore=12,
            splitLongWords=True,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuestionText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=8,
            leftIndent=0.1*inch,
            rightIndent=0.1*inch,
            splitLongWords=True,
            wordWrap='CJK',
            alignment=TA_JUSTIFY
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnswerLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            spaceBefore=6,
            leftIndent=0.1*inch,
            bold=True,
            splitLongWords=True,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnswerText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
            leftIndent=0.15*inch,
            rightIndent=0.1*inch,
            splitLongWords=True,
            wordWrap='CJK',
            alignment=TA_JUSTIFY,
            backColor=colors.HexColor('#f9f9f9'),
            borderColor=colors.HexColor('#e0e0e0'),
            borderWidth=0.5,
            borderPadding=8,
            leading=11
        ))
        
        self.styles.add(ParagraphStyle(
            name='MCOptionText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=4,
            leftIndent=0.2*inch,
            rightIndent=0.1*inch,
            fontName='Courier',
            splitLongWords=True,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CodeText',
            parent=self.styles['Code'],
            fontSize=8,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=8,
            leftIndent=0.15*inch,
            rightIndent=0.1*inch,
            backColor=colors.HexColor('#f5f5f5'),
            borderColor=colors.HexColor('#ddd'),
            borderWidth=1,
            borderPadding=6,
            fontName='Courier',
            leading=9,
            splitLongWords=True,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetadataText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=4,
            leftIndent=0.1*inch,
            rightIndent=0.1*inch,
            splitLongWords=True,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='HeaderMetadata',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6,
            splitLongWords=True,
            wordWrap='CJK'
        ))
    
    def _truncate_text(self, text: str, max_length: int = 500) -> str:
        """Truncate text to prevent overflow"""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML entities for ReportLab"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        return text
    
    def _wrap_text(self, text: str, max_length: int = 400) -> str:
        """Wrap long text to prevent overflow"""
        if len(text) > max_length:
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                if len(" ".join(current_line)) > max_length:
                    lines.append(" ".join(current_line[:-1]))
                    current_line = [word]
            
            if current_line:
                lines.append(" ".join(current_line))
            
            return "<br/>".join(lines)
        
        return text
    
    def _format_mc_question(self, elements: list, question_text: str):
        """Format Multiple Choice question with proper containment"""
        lines = question_text.split('\n')
        
        if lines:
            # Question text (before options)
            q_text = self._sanitize_html(lines[0][:300])
            elements.append(Paragraph(q_text, self.styles['QuestionText']))
            elements.append(Spacer(1, 0.08*inch))
            
            # Options (A, B, C, D)
            for line in lines[1:]:
                if line.strip():
                    option_text = self._sanitize_html(line.strip()[:200])
                    elements.append(Paragraph(option_text, self.styles['MCOptionText']))
            
            elements.append(Spacer(1, 0.1*inch))
    
    def _format_code_question(self, elements: list, question_text: str):
        """Format Code-based question with proper wrapping"""
        question_text = self._sanitize_html(question_text[:400])
        wrapped = self._wrap_text(question_text)
        elements.append(Paragraph(wrapped, self.styles['QuestionText']))
        elements.append(Spacer(1, 0.08*inch))
    
    def _format_code_answer(self, elements: list, answer_text: str):
        """Format code answer with proper containment"""
        if '```' in answer_text:
            parts = answer_text.split('```')
            
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Code block
                    # Truncate long code
                    code_part = part.strip()[:300]
                    code_text = self._sanitize_html(code_part)
                    # Split code into lines to prevent horizontal overflow
                    code_lines = code_text.split('\n')
                    short_lines = [line[:80] for line in code_lines]  # Limit line length
                    formatted_code = "<br/>".join(short_lines)
                    elements.append(Paragraph(formatted_code, self.styles['CodeText']))
                else:  # Regular text
                    if part.strip():
                        text_part = self._sanitize_html(part.strip()[:200])
                        wrapped = self._wrap_text(text_part)
                        elements.append(Paragraph(wrapped, self.styles['QuestionText']))
        else:
            # No code blocks, truncate and wrap
            answer_text = self._sanitize_html(answer_text[:300])
            wrapped = self._wrap_text(answer_text)
            elements.append(Paragraph(wrapped, self.styles['CodeText']))
        
        elements.append(Spacer(1, 0.08*inch))
    
    def _format_answer_text(self, elements: list, answer_text: str, q_type: str):
        """Format answer based on type with proper containment"""
        if q_type in ["Code-based", "Debugging"]:
            self._format_code_answer(elements, answer_text)
        else:
            # Truncate and sanitize
            answer_text = self._sanitize_html(answer_text[:400])
            wrapped = self._wrap_text(answer_text)
            elements.append(Paragraph(wrapped, self.styles['AnswerText']))
            elements.append(Spacer(1, 0.06*inch))
    
    def generate_pdf(self, questions_data: Dict, filename: str, include_metadata: bool = True, 
                    topic: str = "", difficulty: str = "", generic_percentage: int = 60) -> str:
        """Generate PDF with perfect text alignment and containment"""
        os.makedirs("generated_pdfs", exist_ok=True)
        pdf_path = os.path.join("generated_pdfs", f"{filename}.pdf")
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=0.75*inch,
            bottomMargin=0.6*inch,
            title="Interview Questions"
        )
        
        elements = []
        
        # Title
        title_text = self._sanitize_html(f"Interview Questions: {topic[:50]}")
        title = Paragraph(title_text, self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.15*inch))
        
        # Metadata
        if include_metadata:
            generation_time = questions_data.get('generation_time', 'N/A')
            total_questions = questions_data.get('total_questions', 0)
            generic_count = questions_data.get('generic_count', 0)
            practical_count = questions_data.get('practical_count', 0)
            question_types = ", ".join(questions_data.get('question_types', [])[:3])  # Limit types shown
            
            metadata_text = f"""Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
Difficulty: {difficulty} | Types: {question_types} | 
Total: {total_questions} | Generic: {generic_count} ({generic_percentage}%) | Time: {generation_time}s"""
            
            metadata_text = self._sanitize_html(metadata_text)
            elements.append(Paragraph(metadata_text, self.styles['HeaderMetadata']))
            elements.append(Spacer(1, 0.12*inch))
        
        # Questions
        question_count = len(questions_data.get("questions", []))
        
        for idx, question_data in enumerate(questions_data.get("questions", []), 1):
            q_type = question_data.get('type', 'N/A')
            difficulty_q = question_data.get('difficulty', 'N/A')
            
            # Question header
            header_text = f"<b>Q{idx}.</b> {q_type} ({difficulty_q})"
            elements.append(Paragraph(header_text, self.styles['QuestionNumber']))
            
            # Category
            if question_data.get('category'):
                cat_text = self._sanitize_html(f"Category: {question_data['category'][:50]}")
                elements.append(Paragraph(cat_text, self.styles['MetadataText']))
            
            # Question content
            question_text = question_data.get('question', '')
            
            if q_type == "Multiple Choice":
                self._format_mc_question(elements, question_text)
            elif q_type in ["Code-based", "Debugging"]:
                self._format_code_question(elements, question_text)
            else:
                question_text = self._sanitize_html(question_text[:350])
                wrapped = self._wrap_text(question_text)
                elements.append(Paragraph(wrapped, self.styles['QuestionText']))
                elements.append(Spacer(1, 0.06*inch))
            
            # Answer
            if question_data.get('answer'):
                elements.append(Paragraph("<b>Answer:</b>", self.styles['AnswerLabel']))
                answer_text = question_data['answer']
                self._format_answer_text(elements, answer_text, q_type)
            
            # Keywords (truncated)
            if question_data.get('keywords'):
                keywords = ", ".join(question_data['keywords'][:2])  # Limit to 2 keywords
                kw_text = self._sanitize_html(f"Keywords: {keywords}")
                elements.append(Paragraph(kw_text, self.styles['MetadataText']))
            
            elements.append(Spacer(1, 0.15*inch))
            
            # Page break every 2-3 questions to manage space
            if idx % 3 == 0 and idx < question_count:
                elements.append(PageBreak())
        
        # Footer
        elements.append(Spacer(1, 0.15*inch))
        footer_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Questions: {question_count}"
        footer_text = self._sanitize_html(footer_text)
        elements.append(Paragraph(footer_text, self.styles['MetadataText']))
        
        # Build PDF
        try:
            doc.build(elements)
            return pdf_path
        except Exception as e:
            raise Exception(f"Error building PDF: {str(e)}")
