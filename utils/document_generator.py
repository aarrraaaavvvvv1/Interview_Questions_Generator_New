"""Document generation using WeasyPrint (PDF) and python-docx-template (Word)"""

from weasyprint import HTML
from io import BytesIO
from datetime import datetime
from typing import List, Dict
from docxtpl import DocxTemplate
import os

class PDFGenerator:
    """Generate professional PDFs using WeasyPrint"""
    
    def __init__(self, title: str, topic: str):
        """Initialize PDF generator"""
        self.title = title
        self.topic = topic
    
    def generate(self, qa_pairs: List[Dict]) -> bytes:
        """Generate PDF from Q&A pairs using HTML/CSS"""
        
        # Build HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    padding: 40px;
                    background-color: #fff;
                }}
                
                .header {{
                    margin-bottom: 40px;
                    border-bottom: 3px solid #2c3e50;
                    padding-bottom: 20px;
                }}
                
                .header h1 {{
                    font-size: 28px;
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                
                .metadata {{
                    font-size: 12px;
                    color: #666;
                    font-style: italic;
                }}
                
                .metadata p {{
                    margin: 3px 0;
                }}
                
                .question-block {{
                    margin: 30px 0;
                    page-break-inside: avoid;
                }}
                
                .question-number {{
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 8px;
                }}
                
                .question-text {{
                    font-size: 14px;
                    color: #1a1a1a;
                    margin-bottom: 8px;
                    font-weight: 500;
                }}
                
                .type-badge {{
                    display: inline-block;
                    padding: 3px 10px;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    font-style: italic;
                }}
                
                .type-generic {{
                    background-color: #e3f2fd;
                    color: #1565c0;
                    border: 1px solid #90caf9;
                }}
                
                .type-practical {{
                    background-color: #f3e5f5;
                    color: #6a1b9a;
                    border: 1px solid #ce93d8;
                }}
                
                .answer-header {{
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 8px;
                    margin-top: 10px;
                }}
                
                .answer-text {{
                    font-size: 13px;
                    color: #333;
                    line-height: 1.7;
                    background-color: #f5f5f5;
                    padding: 12px;
                    border-left: 3px solid #bbb;
                    border-radius: 2px;
                }}
                
                .separator {{
                    border-bottom: 1px solid #ddd;
                    margin: 20px 0;
                }}
                
                @page {{
                    size: A4;
                    margin: 20px;
                }}
                
                @media print {{
                    body {{
                        padding: 0;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{self.title}</h1>
                <div class="metadata">
                    <p><strong>Topic:</strong> {self.topic}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
                    <p><strong>Total Questions:</strong> {len(qa_pairs)}</p>
                </div>
            </div>
        """
        
        # Add questions
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            type_class = 'type-generic' if qa_type == 'GENERIC' else 'type-practical'
            
            html_content += f"""
            <div class="question-block">
                <div class="question-number">Question {i}</div>
                <div class="question-text">{qa['question']}</div>
                <div class="type-badge {type_class}">[{qa_type}]</div>
                <div class="answer-header">Answer:</div>
                <div class="answer-text">{qa['answer']}</div>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        # Generate PDF using WeasyPrint
        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")


class WordDocumentGenerator:
    """Generate Word documents using docxtpl (template-based)"""
    
    def __init__(self):
        """Initialize Word document generator"""
        self.template_path = "interview_template.docx"
    
    def create_template(self):
        """Create a default template if it doesn't exist"""
        if os.path.exists(self.template_path):
            return True
        
        # Create a basic template using python-docx
        try:
            from docx import Document
            from docx.shared import Pt, RGBColor, Inches
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
            
            doc = Document()
            
            # Add title
            title = doc.add_heading('Interview Questions', 0)
            title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Add metadata
            doc.add_paragraph()
            meta = doc.add_paragraph()
            meta.add_run('Topic: ').bold = True
            meta.add_run('{{ topic }}')
            
            meta2 = doc.add_paragraph()
            meta2.add_run('Generated: ').bold = True
            meta2.add_run('{{ generated_date }}')
            
            doc.add_paragraph()
            
            # Add questions section with Jinja2 template syntax
            doc.add_heading('Questions', level=1)
            
            # Add template marker
            p = doc.add_paragraph('{% for qa in questions %}')
            p.style = 'No Spacing'
            
            doc.add_heading('Question {{ loop.index }}', level=2)
            
            q = doc.add_paragraph('{{ qa.question }}')
            q.runs[0].bold = True
            
            doc.add_paragraph()
            t = doc.add_paragraph()
            t.add_run('Type: ').bold = True
            t.add_run('[{{ qa.type|upper }}]')
            
            doc.add_paragraph()
            
            a = doc.add_paragraph()
            a.add_run('Answer: ').bold = True
            doc.add_paragraph('{{ qa.answer }}')
            
            doc.add_paragraph()
            
            # Add end template marker
            p = doc.add_paragraph('{% endfor %}')
            p.style = 'No Spacing'
            
            # Save template
            doc.save(self.template_path)
            return True
        
        except Exception as e:
            print(f"Warning: Could not create template: {str(e)}")
            return False
    
    def generate(self, qa_pairs: List[Dict], title: str, topic: str) -> bytes:
        """Generate Word document from Q&A pairs"""
        
        # Ensure template exists
        if not os.path.exists(self.template_path):
            if not self.create_template():
                raise Exception(f"Template file not found: {self.template_path}")
        
        try:
            # Load template
            doc = DocxTemplate(self.template_path)
            
            # Prepare context for Jinja2
            context = {
                "topic": topic,
                "generated_date": datetime.now().strftime('%B %d, %Y at %H:%M:%S'),
                "questions": qa_pairs
            }
            
            # Render template
            doc.render(context)
            
            # Save to BytesIO for download
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            raise Exception(f"Error generating Word document: {str(e)}")


def generate_markdown_document(qa_pairs: List[Dict], title: str, topic: str) -> str:
    """Generate markdown formatted document (kept for reference)"""
    md_content = f"""# {title}

**Topic:** {topic}  
**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}  
**Total Questions:** {len(qa_pairs)}

---

"""
    
    for i, qa in enumerate(qa_pairs, 1):
        qa_type = qa.get('type', 'generic').upper()
        type_label = "[GENERIC]" if qa_type == "GENERIC" else "[PRACTICAL]"
        
        md_content += f"""## Question {i}

**{qa['question']}**

**Type:** {type_label}

### Answer

{qa['answer']}

---

"""
    
    return md_content
