"""Document generation for export"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from datetime import datetime
from typing import List, Dict
import io

class PDFGenerator:
    """Generate professional PDF documents with interview questions"""
    
    def __init__(self, title: str, topic: str, curriculum_context: str):
        """Initialize PDF generator"""
        self.title = title
        self.topic = topic
        self.curriculum_context = curriculum_context
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom professional styles"""
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=24,
            spaceBefore=12,
            alignment=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetaInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            spaceAfter=18,
            alignment=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuestionNumber',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuestionText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=8,
            leftIndent=0.2*inch,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='TypeLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6,
            leftIndent=0.2*inch,
            fontName='Helvetica-Oblique'
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnswerHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=4,
            leftIndent=0.2*inch,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnswerText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=16,
            leftIndent=0.2*inch,
            alignment=4,
            fontName='Helvetica'
        ))
    
    def generate(self, qa_pairs: List[Dict]) -> bytes:
        """Generate clean professional PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        story = []
        
        # Title
        story.append(Paragraph(self.title, self.styles['DocumentTitle']))
        
        # Metadata
        meta = f"Topic: {self.topic}<br/>Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
        story.append(Paragraph(meta, self.styles['MetaInfo']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Questions and Answers
        for i, qa in enumerate(qa_pairs, 1):
            # Question number
            story.append(Paragraph(f"Question {i}", self.styles['QuestionNumber']))
            
            # Question text (clean - no markdown symbols)
            question_clean = qa['question'].replace('**', '')
            story.append(Paragraph(question_clean, self.styles['QuestionText']))
            
            # Question type label
            qa_type = qa.get('type', 'generic').upper()
            type_text = "[GENERIC]" if qa_type == "GENERIC" else "[PRACTICAL]"
            story.append(Paragraph(f"Type: {type_text}", self.styles['TypeLabel']))
            
            # Answer header
            story.append(Paragraph("Answer:", self.styles['AnswerHeader']))
            
            # Answer text (clean - no markdown symbols)
            answer_clean = qa['answer'].replace('**', '')
            story.append(Paragraph(answer_clean, self.styles['AnswerText']))
            
            # Page break after every 2 questions
            if i % 2 == 0 and i != len(qa_pairs):
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


def generate_markdown_document(qa_pairs: List[Dict], title: str, topic: str) -> str:
    """Generate markdown formatted document"""
    md_content = f"""# {title}

**Topic:** {topic}  
**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}

---

"""
    
    for i, qa in enumerate(qa_pairs, 1):
        qa_type = qa.get('type', 'generic').upper()
        type_label = "[GENERIC]" if qa_type == "GENERIC" else "[PRACTICAL]"
        
        md_content += f"""## Question {i}

{qa['question'].replace('**', '')}

**Type:** {type_label}

### Answer

{qa['answer'].replace('**', '')}

---

"""
    
    return md_content
