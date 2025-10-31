from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from typing import Dict
from datetime import datetime
import os

class PDFGenerator:
    """Generates PDF documents from questions data"""
    
    def __init__(self):
        self.page_size = letter
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        self.styles.add(ParagraphStyle(name='CustomTitle', parent=self.styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1f77b4'), spaceAfter=30, alignment=1))
        self.styles.add(ParagraphStyle(name='QuestionStyle', parent=self.styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2c3e50'), spaceAfter=12, spaceBefore=12))
        self.styles.add(ParagraphStyle(name='AnswerStyle', parent=self.styles['Normal'], fontSize=10, leftIndent=20, rightIndent=20, spaceAfter=15, textColor=colors.HexColor('#34495e')))
        self.styles.add(ParagraphStyle(name='MetadataStyle', parent=self.styles['Normal'], fontSize=9, textColor=colors.grey))
    
    def generate_pdf(self, questions_data: Dict, filename: str, include_metadata: bool = True, topic: str = "", difficulty: str = "", generic_percentage: int = 60) -> str:
        os.makedirs("generated_pdfs", exist_ok=True)
        pdf_path = os.path.join("generated_pdfs", f"{filename}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=self.page_size, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=1*inch, bottomMargin=0.75*inch)
        
        elements = []
        title = Paragraph(f"Interview Questions: {topic}", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        if include_metadata:
            metadata_text = self._create_metadata(questions_data, difficulty, generic_percentage)
            elements.append(metadata_text)
            elements.append(Spacer(1, 0.2*inch))
        
        for idx, question_data in enumerate(questions_data.get("questions", []), 1):
            question_text = f"<b>Q{idx}. {question_data.get('question', '')}</b>"
            elements.append(Paragraph(question_text, self.styles['QuestionStyle']))
            
            metadata = []
            if question_data.get('type'):
                metadata.append(f"Type: {question_data['type']}")
            if question_data.get('difficulty'):
                metadata.append(f"Difficulty: {question_data['difficulty']}")
            if 'is_generic' in question_data:
                category = "Generic" if question_data['is_generic'] else "Practical"
                metadata.append(f"Category: {category}")
            
            if metadata:
                meta_text = " | ".join(metadata)
                elements.append(Paragraph(meta_text, self.styles['MetadataStyle']))
            
            if question_data.get('answer'):
                answer_text = f"<b>Answer:</b> {question_data['answer']}"
                elements.append(Paragraph(answer_text, self.styles['AnswerStyle']))
            
            if question_data.get('keywords'):
                keywords_text = f"<i>Keywords: {', '.join(question_data['keywords'])}</i>"
                elements.append(Paragraph(keywords_text, self.styles['MetadataStyle']))
            
            elements.append(Spacer(1, 0.2*inch))
            if idx % 5 == 0 and idx < len(questions_data.get("questions", [])):
                elements.append(PageBreak())
        
        elements.append(Spacer(1, 0.3*inch))
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Questions: {len(questions_data.get('questions', []))}"
        elements.append(Paragraph(footer_text, self.styles['MetadataStyle']))
        doc.build(elements)
        return pdf_path
    
    def _create_metadata(self, questions_data: Dict, difficulty: str, generic_percentage: int) -> Paragraph:
        generation_time = questions_data.get('generation_time', 'N/A')
        total_questions = questions_data.get('total_questions', 0)
        generic_count = questions_data.get('generic_count', 0)
        practical_count = questions_data.get('practical_count', 0)
        metadata = f"<b>Document Information:</b><br/>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Difficulty Level: {difficulty}<br/>Total Questions: {total_questions}<br/>Generic Questions: {generic_count} ({generic_percentage}%)<br/>Practical Questions: {practical_count} ({100-generic_percentage}%)<br/>Generation Time: {generation_time}s<br/>"
        return Paragraph(metadata, self.styles['Normal'])
