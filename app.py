import streamlit as st
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.gemini_service import GeminiService
    from utils.firecrawl_service import FireCrawlService
    from utils.prompt_templates import get_question_generation_prompt
    from utils.document_generator import PDFGenerator, generate_markdown_document
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

# Sidebar - API Configuration
st.sidebar.title("🔑 API Keys")
st.sidebar.markdown("Enter your API keys")

gemini_api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    placeholder="Enter Gemini API key",
    help="Get from: https://aistudio.google.com/app/apikey"
)

firecrawl_api_key = st.sidebar.text_input(
    "FireCrawl API Key",
    type="password",
    placeholder="Enter FireCrawl API key",
    help="Get from: https://www.firecrawl.dev"
)

# Main content
st.title("📋 Interview Questions Generator")
st.markdown("Generate professional interview questions from curriculum content")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📝 Generate", "📚 Review", "📥 Export"])

# Tab 1: Generate Questions
with tab1:
    st.header("Generate Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input(
            "Topic Name",
            placeholder="e.g., Machine Learning Algorithms",
            help="Main topic for question generation"
        )
        
        num_questions = st.slider(
            "Number of Questions",
            min_value=MIN_QUESTIONS,
            max_value=MAX_QUESTIONS,
            value=10,
            step=1,
            help="Total questions to generate"
        )
    
    with col2:
        difficulty = st.selectbox(
            "Difficulty Level",
            DIFFICULTY_LEVELS,
            help="Question complexity level"
        )
        
        practical_percentage = st.slider(
            "Practical Questions %",
            min_value=MIN_PRACTICAL_PERCENTAGE,
            max_value=MAX_PRACTICAL_PERCENTAGE,
            value=60,
            step=5,
            help="Percentage of practical/business-based questions (rest will be generic)"
        )
    
    st.markdown("---")
    
    curriculum_context = st.text_area(
        "Curriculum Content",
        placeholder="Paste the curriculum/course content here...\n\nExample:\nClassical algorithms: linear regression, logistic regression, decision trees.\nEnsembles & boosting: random forest, XGBoost.\nModel evaluation: confusion matrix, ROC/AUC, precision/recall.",
        height=150,
        help="Detailed curriculum content for question generation"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    
    with col1:
        generate_btn = st.button(
            "🚀 Generate",
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        clear_btn = st.button(
            "🔄 Clear",
            use_container_width=True
        )
    
    if clear_btn:
        st.session_state.qa_pairs = None
        st.session_state.generated_topic = None
        st.rerun()
    
    # Generation logic
    if generate_btn:
        # Validation
        if not gemini_api_key:
            st.error("❌ Please enter Gemini API key")
        elif not firecrawl_api_key:
            st.error("❌ Please enter FireCrawl API key")
        elif not topic or not curriculum_context:
            st.error("❌ Please fill in Topic and Curriculum Content")
        else:
            with st.spinner("⏳ Generating questions..."):
                try:
                    # Initialize services
                    gemini_service = GeminiService(gemini_api_key)
                    firecrawl_service = FireCrawlService(firecrawl_api_key)
                    
                    web_content = ""
                    
                    # Fetch web content for current information
                    with st.spinner("🔍 Researching topic..."):
                        try:
                            search_query = f"{topic} latest {difficulty.lower()} 2024 2025"
                            search_results = firecrawl_service.search_and_scrape(search_query)
                            if search_results:
                                web_content = "\n\n".join([
                                    f"Source: {r['title']}\n{r['content'][:500]}"
                                    for r in search_results[:2]
                                ])
                        except Exception as e:
                            st.warning(f"Could not fetch web content: {str(e)}")
                    
                    # Generate prompt with exact distribution
                    prompt = get_question_generation_prompt(
                        topic, 
                        curriculum_context, 
                        num_questions,
                        practical_percentage, 
                        difficulty,
                        web_content
                    )
                    
                    # Generate questions
                    response = gemini_service.generate_questions(prompt)
                    qa_pairs = gemini_service.parse_qa_pairs(response)
                    
                    if not qa_pairs:
                        st.error("❌ No questions generated. Try again.")
                    else:
                        # Verify distribution
                        practical_count = sum(1 for q in qa_pairs if q.get('type') == 'practical')
                        generic_count = len(qa_pairs) - practical_count
                        
                        st.session_state.qa_pairs = qa_pairs
                        st.session_state.generated_topic = topic
                        
                        st.success(f"✅ Generated {len(qa_pairs)} questions")
                        st.info(f"Distribution: {generic_count} generic, {practical_count} practical")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 2: Review Questions
with tab2:
    st.header("Review & Edit Questions")
    
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first")
    else:
        st.success(f"✅ {len(st.session_state.qa_pairs)} questions for: {st.session_state.generated_topic}")
        
        for i, qa in enumerate(st.session_state.qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            with st.expander(f"Q{i}: {qa['question'][:60]}... [{qa_type}]"):
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.caption(f"Type: {qa_type}")
                
                with col2:
                    st.caption(f"ID: {qa['id']}")
                
                st.markdown("**Question**")
                edited_q = st.text_area(
                    "Edit:",
                    value=qa['question'],
                    height=80,
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )
                
                st.markdown("**Answer**")
                edited_a = st.text_area(
                    "Edit:",
                    value=qa['answer'],
                    height=120,
                    key=f"a_{i}",
                    label_visibility="collapsed"
                )
                
                if edited_q != qa['question'] or edited_a != qa['answer']:
                    st.session_state.qa_pairs[i-1]['question'] = edited_q
                    st.session_state.qa_pairs[i-1]['answer'] = edited_a
                    st.success("✅ Updated")

# Tab 3: Export
with tab3:
    st.header("Export Questions")
    
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first")
    else:
        st.success(f"✅ Ready to export {len(st.session_state.qa_pairs)} questions")
        
        export_format = st.selectbox(
            "Export Format",
            ["PDF", "Markdown", "Text"],
            help="Choose export format"
        )
        
        if export_format == "PDF":
            pdf_title = st.text_input(
                "Document Title",
                value=DOCUMENT_TITLE_FORMAT.format(topic=st.session_state.generated_topic)
            )
            
            if st.button("📥 Download as PDF", use_container_width=True):
                try:
                    pdf_gen = PDFGenerator(
                        pdf_title,
                        st.session_state.generated_topic,
                        "Professional Interview Questions"
                    )
                    pdf_bytes = pdf_gen.generate(st.session_state.qa_pairs)
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_bytes,
                        file_name=f"{pdf_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        elif export_format == "Markdown":
            md_content = generate_markdown_document(
                st.session_state.qa_pairs,
                f"Interview Questions - {st.session_state.generated_topic}",
                st.session_state.generated_topic
            )
            
            st.download_button(
                label="📥 Download Markdown",
                data=md_content,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
            
            st.markdown("### Preview")
            st.markdown(md_content)
        
        else:  # Text
            text_content = ""
            for i, qa in enumerate(st.session_state.qa_pairs, 1):
                text_content += f"QUESTION {i}:\n{qa['question']}\n\nANSWER {i}:\n{qa['answer']}\n\n{'='*80}\n\n"
            
            st.download_button(
                label="📥 Download Text",
                data=text_content,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
