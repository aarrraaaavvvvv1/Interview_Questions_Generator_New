import streamlit as st
from datetime import datetime
import sys
import os
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.gemini_service import GeminiService
    from utils.firecrawl_service import FireCrawlService
    from utils.prompt_templates import get_question_generation_prompt
    from utils.document_generator import PDFGenerator, WordDocumentGenerator
    from config import (
        DIFFICULTY_LEVELS, MIN_QUESTIONS, MAX_QUESTIONS,
        MIN_PRACTICAL_PERCENTAGE, MAX_PRACTICAL_PERCENTAGE, DOCUMENT_TITLE_FORMAT
    )
except ImportError as e:
    st.error(f"Import Error: {str(e)}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="Interview Questions Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'qa_pairs' not in st.session_state:
    st.session_state.qa_pairs = None
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = None
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
if 'word_bytes' not in st.session_state:
    st.session_state.word_bytes = None
if 'last_params' not in st.session_state:
    st.session_state.last_params = None
if 'partner_institute' not in st.session_state:
    st.session_state.partner_institute = "IIT Kanpur"

# Sidebar
st.sidebar.title("🔑 API Keys")
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")
firecrawl_api_key = st.sidebar.text_input("FireCrawl API Key", type="password")

# Main content
st.title("📋 Interview Questions Generator")

# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Generate", "📚 Review", "📥 Export"])

# Tab 1: Generate
with tab1:
    st.header("Generate Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input("Topic Name")
        num_questions = st.slider("Number of Questions", MIN_QUESTIONS, MAX_QUESTIONS, 10)
    
    with col2:
        difficulty = st.selectbox("Difficulty Level", DIFFICULTY_LEVELS)
        practical_percentage = st.slider("Practical Questions %", MIN_PRACTICAL_PERCENTAGE, MAX_PRACTICAL_PERCENTAGE, 60, 5)
    
    partner_institute = st.selectbox("Partner Institute", ["IIT Kanpur", "IIT Guwahati"])
    st.session_state.partner_institute = partner_institute
    
    st.markdown("---")
    curriculum_context = st.text_area("Curriculum Content", height=150)
    st.markdown("---")
    
    current_params = {
        'topic': topic, 'num_questions': num_questions, 'practical_percentage': practical_percentage,
        'difficulty': difficulty, 'curriculum': curriculum_context, 'partner': partner_institute
    }
    
    if st.session_state.last_params is not None and current_params != st.session_state.last_params:
        st.session_state.qa_pairs = None
        st.session_state.pdf_bytes = None
        st.session_state.word_bytes = None
    
    col1, col2 = st.columns([1, 5])
    
    with col1:
        generate_btn = st.button("🚀 Generate", use_container_width=True, type="primary")
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.qa_pairs = None
            st.session_state.pdf_bytes = None
            st.session_state.word_bytes = None
            st.session_state.last_params = None
            st.rerun()
    
    if generate_btn:
        if not gemini_api_key or not firecrawl_api_key:
            st.error("❌ Please enter API keys")
        elif not topic or not curriculum_context:
            st.error("❌ Please fill in Topic and Curriculum")
        else:
            with st.spinner("⏳ Generating..."):
                try:
                    st.session_state.pdf_bytes = None
                    st.session_state.word_bytes = None
                    st.session_state.last_params = current_params
                    
                    gemini_service = GeminiService(gemini_api_key)
                    firecrawl_service = FireCrawlService(firecrawl_api_key)
                    
                    web_content = ""
                    try:
                        search_results = firecrawl_service.search_and_scrape(f"{topic} latest {difficulty.lower()} 2024")
                        if search_results:
                            web_content = "\n\n".join([f"Source: {r['title']}\n{r['content'][:500]}" for r in search_results[:2]])
                    except:
                        pass
                    
                    prompt = get_question_generation_prompt(topic, curriculum_context, num_questions, practical_percentage, difficulty, web_content)
                    
                    max_retries = 3
                    qa_pairs = []
                    for attempt in range(max_retries):
                        if attempt > 0:
                            st.info(f"🔄 Retry {attempt}/{max_retries-1}...")
                        response = gemini_service.generate_questions(prompt)
                        qa_pairs = gemini_service.parse_qa_pairs(response, num_questions)
                        if len(qa_pairs) == num_questions:
                            break
                    
                    if len(qa_pairs) == num_questions:
                        st.session_state.qa_pairs = qa_pairs
                        st.session_state.generated_topic = topic
                        st.success(f"✅ Generated {len(qa_pairs)} questions!")
                    else:
                        st.error(f"❌ Generated {len(qa_pairs)} but requested {num_questions}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 2: Review
with tab2:
    st.header("Review & Edit")
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first")
    else:
        for i, qa in enumerate(st.session_state.qa_pairs, 1):
            with st.expander(f"Q{i}: {qa['question'][:60]}..."):
                edited_q = st.text_area("Question", qa['question'], height=80, key=f"q_{i}")
                edited_a = st.text_area("Answer", qa['answer'], height=120, key=f"a_{i}")
                if edited_q != qa['question'] or edited_a != qa['answer']:
                    st.session_state.qa_pairs[i-1]['question'] = edited_q
                    st.session_state.qa_pairs[i-1]['answer'] = edited_a
                    st.session_state.pdf_bytes = None
                    st.session_state.word_bytes = None

# Tab 3: Export
with tab3:
    st.header("Export")
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first")
    else:
        export_format = st.selectbox("Export Format", ["PDF", "Word Document"])
        
        if export_format == "PDF":
            pdf_title = st.text_input("Title", DOCUMENT_TITLE_FORMAT.format(topic=st.session_state.generated_topic), key="pdf_title")
            
            if st.button("🔄 Generate PDF", use_container_width=True):
                try:
                    with st.spinner("Generating PDF..."):
                        pdf_gen = PDFGenerator(pdf_title, st.session_state.generated_topic, st.session_state.partner_institute)
                        st.session_state.pdf_bytes = pdf_gen.generate(st.session_state.qa_pairs)
                        st.success("✅ PDF generated!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.session_state.pdf_bytes:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button("📥 Download PDF", st.session_state.pdf_bytes, f"{pdf_title}_{timestamp}.pdf", "application/pdf")
                
                # PDF PREVIEW
                st.markdown("### 📄 PDF Preview")
                base64_pdf = base64.b64encode(st.session_state.pdf_bytes).decode('utf-8')
                pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf">'
                st.markdown(pdf_display, unsafe_allow_html=True)
        
        else:
            doc_title = st.text_input("Title", DOCUMENT_TITLE_FORMAT.format(topic=st.session_state.generated_topic), key="doc_title")
            
            if st.button("🔄 Generate Word", use_container_width=True):
                try:
                    with st.spinner("Generating Word..."):
                        word_gen = WordDocumentGenerator()
                        st.session_state.word_bytes = word_gen.generate(st.session_state.qa_pairs, doc_title, st.session_state.generated_topic, st.session_state.partner_institute)
                        st.success("✅ Word generated!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.session_state.word_bytes:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button("📥 Download Word", st.session_state.word_bytes, f"{doc_title}_{timestamp}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
