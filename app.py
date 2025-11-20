import streamlit as st
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.gemini_service import GeminiService
    from utils.firecrawl_service import FireCrawlService
    from utils.prompt_templates import get_question_generation_prompt
    from utils.document_generator import PDFGenerator, WordDocumentGenerator
    from config import (
        DIFFICULTY_LEVELS, MIN_QUESTIONS, MAX_QUESTIONS,
        MIN_PRACTICAL_PERCENTAGE, MAX_PRACTICAL_PERCENTAGE
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
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password", placeholder="Enter Gemini API key")
firecrawl_api_key = st.sidebar.text_input("FireCrawl API Key", type="password", placeholder="Enter FireCrawl API key")

# Main content
st.title("📋 Interview Questions Generator")

# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Generate", "📚 Review", "📥 Export"])

# Tab 1: Generate
with tab1:
    st.header("Generate Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input("Topic Name", placeholder="e.g., Machine Learning Algorithms")
        num_questions = st.slider("Number of Questions", MIN_QUESTIONS, MAX_QUESTIONS, 10, 1)
    
    with col2:
        difficulty = st.selectbox("Difficulty Level", DIFFICULTY_LEVELS)
        practical_percentage = st.slider("Practical Questions %", MIN_PRACTICAL_PERCENTAGE, MAX_PRACTICAL_PERCENTAGE, 60, 5)
    
    partner_institute = st.selectbox("Partner Institute", ["IIT Kanpur", "IIT Guwahati"])
    st.session_state.partner_institute = partner_institute
    
    st.markdown("---")
    curriculum_context = st.text_area("Curriculum Content", height=150, placeholder="Paste curriculum content here...")
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
            with st.spinner("⏳ Generating questions..."):
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
                        practical_count = sum(1 for q in qa_pairs if q.get('type') == 'practical')
                        generic_count = len(qa_pairs) - practical_count
                        st.success(f"✅ Generated {len(qa_pairs)} questions!")
                        st.info(f"Distribution: {generic_count} generic, {practical_count} practical")
                    else:
                        st.error(f"❌ Generated {len(qa_pairs)} but requested {num_questions}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 2: Review
with tab2:
    st.header("Review & Edit Questions")
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first")
    else:
        st.success(f"✅ {len(st.session_state.qa_pairs)} questions for: {st.session_state.generated_topic}")
        for i, qa in enumerate(st.session_state.qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            with st.expander(f"Q{i}: {qa['question'][:60]}... [{qa_type}]"):
                edited_q = st.text_area("Question", qa['question'], height=80, key=f"q_{i}")
                edited_a = st.text_area("Answer", qa['answer'], height=120, key=f"a_{i}")
                if edited_q != qa['question'] or edited_a != qa['answer']:
                    st.session_state.qa_pairs[i-1]['question'] = edited_q
                    st.session_state.qa_pairs[i-1]['answer'] = edited_a
                    st.session_state.pdf_bytes = None
                    st.session_state.word_bytes = None
                    st.success("✅ Updated")

# Tab 3: Export
with tab3:
    st.header("Export Questions")
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first")
    else:
        st.success(f"✅ Ready to export {len(st.session_state.qa_pairs)} questions")
        
        export_format = st.selectbox("Export Format", ["PDF", "Word Document"])
        
        # Document title is auto-generated: "Interview Questions" + topic
        doc_title = "Interview Questions"
        doc_topic = st.session_state.generated_topic
        
        if export_format == "PDF":
            st.markdown("### PDF Export")
            
            if st.button("🔄 Generate PDF", use_container_width=True, key="gen_pdf_btn"):
                try:
                    with st.spinner("Generating PDF..."):
                        pdf_gen = PDFGenerator(doc_title, doc_topic, st.session_state.partner_institute)
                        st.session_state.pdf_bytes = pdf_gen.generate(st.session_state.qa_pairs)
                        st.success("✅ PDF generated!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.session_state.pdf_bytes:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"Interview_Questions_{doc_topic.replace(' ', '_')}_{timestamp}.pdf"
                st.download_button(
                    label="📥 Download PDF",
                    data=st.session_state.pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    key="download_pdf_btn"
                )
        
        else:
            st.markdown("### Word Document Export")
            
            if st.button("🔄 Generate Word Document", use_container_width=True, key="gen_word_btn"):
                try:
                    with st.spinner("Generating Word document..."):
                        word_gen = WordDocumentGenerator()
                        st.session_state.word_bytes = word_gen.generate(st.session_state.qa_pairs, doc_title, doc_topic, st.session_state.partner_institute)
                        st.success("✅ Word document generated!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.session_state.word_bytes:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"Interview_Questions_{doc_topic.replace(' ', '_')}_{timestamp}.docx"
                st.download_button(
                    label="📥 Download Word Document",
                    data=st.session_state.word_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_word_btn"
                )
                st.info("💡 Download the Word document to edit locally")
