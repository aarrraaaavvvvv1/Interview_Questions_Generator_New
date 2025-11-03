from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from typing import Dict
from datetime import datetime
import os
import re

class PDFGenerator:
    """Generates perfectly formatted PDF documents from questions data"""
    
    def __init__(self):
        self.page_size = letter
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom styles for different question types"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuestionStyle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=15
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnswerStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=15,
            rightIndent=15,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e'),
            backColor=colors.HexColor('#f9f9f9')
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetadataStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='MCOptionStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceBefore=3,
            spaceAfter=3,
            fontName='Courier'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CodeStyle',
            parent=self.styles['Code'],
            fontSize=9,
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor('#f5f5f5'),
            borderColor=colors.HexColor('#ddd'),
            borderWidth=1,
            borderPadding=10,
            fontName='Courier'
        ))
    
    def _format_question_for_pdf(self, question_text: str, q_type: str) -> list:
        """Format question based on type for PDF"""
        elements = []
        
        if q_type == "Multiple Choice":
            # Split question and options
            lines = question_text.split('\n')
            if lines:
                # Question text (before options)
                question_part = lines[0]
                elements.append(Paragraph(question_part, self.styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
                
                # Options (A, B, C, D)
                for line in lines[1:]:
                    if line.strip():
                        elements.append(Paragraph(line, self.styles['MCOptionStyle']))
        
        elif q_type in ["Code-based", "Debugging"]:
            # Handle code in question
            if '```' in question_text:
                parts = question_text.split('```')
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Code block
                        elements.append(Preformatted(part.strip(), self.styles['CodeStyle']))
                    else:  # Regular text
                        if part.strip():
                            elements.append(Paragraph(part.strip(), self.styles['Normal']))
            else:
                elements.append(Paragraph(question_text, self.styles['Normal']))
        
        else:
            # Regular question types
            elements.append(Paragraph(question_text, self.styles['Normal']))
        
        return elements
    
    def _format_answer_for_pdf(self, answer_text: str, q_type: str) -> list:
        """Format answer based on type for PDF"""
        elements = []
        
        if q_type in ["Code-based", "Debugging"]:
            # Extract code blocks from answer
            if '```' in answer_text:
                parts = answer_text.split('```')
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Code block
                        elements.append(Spacer(1, 0.05*inch))
                        elements.append(Preformatted(part.strip(), self.styles['CodeStyle']))
                        elements.append(Spacer(1, 0.05*inch))
                    else:  # Regular text
                        if part.strip():
                            elements.append(Paragraph(f"<b>Answer:</b> {part.strip()}", self.styles['AnswerStyle']))
            else:
                elements.append(Preformatted(answer_text, self.styles['CodeStyle']))
        
        elif q_type == "Multiple Choice":
            # Format MC answer with highlighting
            elements.append(Paragraph(f"<b>Answer:</b> {answer_text}", self.styles['AnswerStyle']))
        
        else:
            # Regular answer
            elements.append(Paragraph(f"<b>Answer:</b> {answer_text}", self.styles['AnswerStyle']))
        
        return elements
    
    def generate_pdf(self, questions_data: Dict, filename: str, include_metadata: bool = True, topic: str = "", difficulty: str = "", generic_percentage: int = 60) -> str:
        """Generate PDF with perfect formatting for all question types"""
        os.makedirs("generated_pdfs", exist_ok=True)
        pdf_path = os.path.join("generated_pdfs", f"{filename}.pdf")
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=self.page_size,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        elements = []
        
        # Title
        title = Paragraph(f"Interview Questions: {topic}", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Metadata
        if include_metadata:
            metadata_text = self._create_metadata(questions_data, difficulty, generic_percentage)
            elements.append(metadata_text)
            elements.append(Spacer(1, 0.2*inch))
        
        # Questions
        for idx, question_data in enumerate(questions_data.get("questions", []), 1):
            q_type = question_data.get('type', 'N/A')
            
            # Question number and type
            question_header = f"<b>Question {idx}</b> ({q_type} - {question_data.get('difficulty', 'N/A')})"
            elements.append(Paragraph(question_header, self.styles['QuestionStyle']))
            
            # Category
            if question_data.get('category'):
                category_text = f"<i>Category: {question_data['category']}</i>"
                elements.append(Paragraph(category_text, self.styles['MetadataStyle']))
                elements.append(Spacer(1, 0.05*inch))
            
            # Question content
            question_text = question_data.get('question', '')
            question_elements = self._format_question_for_pdf(question_text, q_type)
            for elem in question_elements:
                elements.append(elem)
            
            elements.append(Spacer(1, 0.1*inch))
            
            # Answer
            if question_data.get('answer'):
                answer_text = question_data['answer']
                answer_elements = self._format_answer_for_pdf(answer_text, q_type)
                for elem in answer_elements:
                    elements.append(elem)
            
            # Keywords
            if question_data.get('keywords'):
                keywords_text = f"<i>Keywords: {', '.join(question_data['keywords'])}</i>"
                elements.append(Spacer(1, 0.05*inch))
                elements.append(Paragraph(keywords_text, self.styles['MetadataStyle']))
            
            elements.append(Spacer(1, 0.2*inch))
            
            # Page break every 3 questions (except last)
            if idx % 3 == 0 and idx < len(questions_data.get("questions", [])):
                elements.append(PageBreak())
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Questions: {len(questions_data.get('questions', []))}"
        elements.append(Paragraph(footer_text, self.styles['MetadataStyle']))
        
        # Build PDF
        doc.build(elements)
        return pdf_path
    
    def _create_metadata(self, questions_data: Dict, difficulty: str, generic_percentage: int) -> Paragraph:
        """Create metadata section for PDF"""
        generation_time = questions_data.get('generation_time', 'N/A')
        total_questions = questions_data.get('total_questions', 0)
        generic_count = questions_data.get('generic_count', 0)
        practical_count = questions_data.get('practical_count', 0)
        question_types = ", ".join(questions_data.get('question_types', []))
        
        metadata = f"""<b>Document Information:</b><br/>
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
Difficulty Level: {difficulty}<br/>
Question Types: {question_types}<br/>
Total Questions: {total_questions}<br/>
Generic Questions: {generic_count} ({generic_percentage}%)<br/>
Practical Questions: {practical_count} ({100-generic_percentage}%)<br/>
Generation Time: {generation_time}s"""
        
        return Paragraph(metadata, self.styles['Normal'])
