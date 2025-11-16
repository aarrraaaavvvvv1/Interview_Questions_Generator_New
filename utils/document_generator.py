"""Document generation for export"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
from typing import List, Dict
import io

class PDFGenerator:
    """Generate PDF documents with interview questions"""
    
    def __init__(self, title: str, topic: str, curriculum_context: str):
        """Initialize PDF generator"""
        self.title = title
        self.topic = topic
        self.curriculum_context = curriculum_context
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom styles to document"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuestionStyle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#000066'),
            spaceAfter=12,
            spaceBefore=12,
            borderColor=colors.HexColor('#000066'),
            borderWidth=0.5,
            borderPadding=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnswerStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=24,
            alignment=4  # Left alignment with justified text
        ))
    
    def generate(self, qa_pairs: List[Dict], filename: str = None) -> bytes:
        """Generate PDF and return bytes"""
        if filename is None:
            filename = f"Interview_Questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Add title
        story.append(Paragraph(self.title, self.styles['CustomTitle']))
        story.append(Paragraph(f"Topic: <b>{self.topic}</b>", self.styles['Normal']))
        story.append(Paragraph(f"Curriculum Context: <b>{self.curriculum_context}</b>", self.styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("=" * 80, self.styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Add Q&A pairs
        for i, qa in enumerate(qa_pairs, 1):
            # Question
            question_text = f"<b>Question {i}:</b> {qa['question']}"
            story.append(Paragraph(question_text, self.styles['QuestionStyle']))
            
            # Question type badge
            qa_type = qa.get('type', 'generic').upper()
            type_color = '#006600' if qa_type == 'PRACTICAL' else '#000066'
            story.append(Paragraph(f"<font color='{type_color}'>[{qa_type}]</font>", self.styles['Normal']))
            
            story.append(Spacer(1, 0.1 * inch))
            
            # Answer
            answer_text = f"<b>Answer:</b> {qa['answer']}"
            story.append(Paragraph(answer_text, self.styles['AnswerStyle']))
            
            story.append(Spacer(1, 0.2 * inch))
            
            # Add page break after every 3 questions
            if i % 3 == 0 and i != len(qa_pairs):
                story.append(PageBreak())
        
        # Add footer
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("=" * 80, self.styles['Normal']))
        story.append(Paragraph("For Educational Purposes | IIT/IIM Collaborative Course Material", 
                             self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


def generate_markdown_document(qa_pairs: List[Dict], title: str, topic: str, 
                              curriculum_context: str) -> str:
    """Generate markdown formatted document"""
    md_content = f"""# {title}

**Topic:** {topic}  
**Curriculum Context:** {curriculum_context}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    for i, qa in enumerate(qa_pairs, 1):
        qa_type = qa.get('type', 'generic').upper()
        md_content += f"""## Question {i}
**Type:** {qa_type}

### Question
{qa['question']}

### Answer
{qa['answer']}

---

"""
    
    md_content += """\n*For Educational Purposes | IIT/IIM Collaborative Course Material*"""
    
    return md_content
