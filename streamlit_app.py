import streamlit as st
from datetime import datetime

# Import utility modules
from utils.gemini_service import GeminiService
from utils.firecrawl_service import FireCrawlService
from utils.prompt_templates import get_question_generation_prompt, get_web_content_prompt
from utils.document_generator import PDFGenerator, generate_markdown_document
from config import (
    QUESTION_TYPES, DIFFICULTY_LEVELS, MIN_QUESTIONS, MAX_QUESTIONS,
    MIN_PERCENTAGE, MAX_PERCENTAGE, DOCUMENT_TITLE_FORMAT
)

# Configure page
st.set_page_config(
    page_title="Interview Questions Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'qa_pairs' not in st.session_state:
    st.session_state.qa_pairs = None
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = None

# Sidebar - API Configuration (User Input)
st.sidebar.title("🔑 API Configuration")
st.sidebar.markdown("Enter your API keys below")

gemini_api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    placeholder="paste-your-gemini-api-key-here",
    help="Get your API key from: https://aistudio.google.com/app/apikey"
)

firecrawl_api_key = st.sidebar.text_input(
    "FireCrawl API Key (Optional)",
    type="password",
    placeholder="paste-your-firecrawl-api-key-here",
    help="Get your API key from: https://www.firecrawl.dev (optional for web scraping)"
)

use_web_sources = st.sidebar.checkbox(
    "Use Web Sources",
    value=False,
    help="Fetch latest information from web using FireCrawl"
)

# Main content
st.title("🎯 Interview Questions Generator")
st.markdown("""
Generate high-quality interview questions for professional study materials.
Perfect for IIT/IIM collaborative courses targeting working professionals.
""")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📝 Generate Questions", "📚 View & Edit", "📥 Export"])

# Tab 1: Generate Questions
with tab1:
    st.header("Generate Interview Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input(
            "📌 Topic Name",
            placeholder="e.g., Cloud Computing, Machine Learning, Microservices",
            help="The main topic for which you want to generate questions"
        )
        
        curriculum_context = st.text_area(
            "🎓 Curriculum Context",
            placeholder="e.g., Advanced Python for Enterprise Solutions",
            height=100,
            help="Provide context about the curriculum or course"
        )
    
    with col2:
        difficulty = st.selectbox(
            "📊 Difficulty Level",
            DIFFICULTY_LEVELS,
            help="Choose the difficulty level for questions"
        )
        
        num_questions = st.slider(
            "🔢 Number of Questions",
            min_value=MIN_QUESTIONS,
            max_value=MAX_QUESTIONS,
            value=10,
            help="Total number of questions to generate"
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        generic_percentage = st.slider(
            "📖 Generic Questions (%)",
            min_value=MIN_PERCENTAGE,
            max_value=MAX_PERCENTAGE,
            value=40,
            step=5,
            help="Percentage of general knowledge questions"
        )
    
    with col2:
        practical_percentage = st.slider(
            "💼 Practical/Business Questions (%)",
            min_value=MIN_PERCENTAGE,
            max_value=MAX_PERCENTAGE,
            value=60,
            step=5,
            help="Percentage of practical and business-based questions"
        )
    
    # Validate percentage distribution
    if generic_percentage + practical_percentage != 100:
        st.warning(f"⚠️ Percentages add up to {generic_percentage + practical_percentage}%. They should equal 100%.")
    
    # Web source options
    if use_web_sources:
        st.markdown("---")
        web_search_query = st.text_input(
            "🔍 Web Search Query",
            placeholder="e.g., Latest trends in cloud computing 2025",
            help="Specific search query for fetching latest web content"
        )
    
    st.markdown("---")
    
    # Generate button
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        generate_btn = st.button(
            "🚀 Generate Questions",
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
            st.error("❌ Please enter your Gemini API Key in the sidebar")
        elif not topic or not curriculum_context:
            st.error("❌ Please fill in all required fields (Topic and Curriculum Context)")
        elif generic_percentage + practical_percentage != 100:
            st.error("❌ Generic and Practical percentages must add up to 100%")
        else:
            with st.spinner("🔄 Generating interview questions..."):
                try:
                    # Initialize Gemini service
                    gemini_service = GeminiService(gemini_api_key)
                    
                    web_content = ""
                    
                    # Fetch web content if requested
                    if use_web_sources and web_search_query:
                        if not firecrawl_api_key:
                            st.warning("⚠️ FireCrawl API key not provided. Skipping web content.")
                        else:
                            with st.spinner("🕷️ Fetching web content..."):
                                try:
                                    firecrawl_service = FireCrawlService(firecrawl_api_key)
                                    search_results = firecrawl_service.search_and_scrape(web_search_query)
                                    web_content = "\n\n".join([
                                        f"Source: {r['title']}\nURL: {r['url']}\n{r['content']}"
                                        for r in search_results[:3]
                                    ])
                                except Exception as e:
                                    st.warning(f"⚠️ Could not fetch web content: {str(e)}")
                    
                    # Generate prompt
                    if web_content:
                        prompt = get_web_content_prompt(
                            web_content, topic, curriculum_context, num_questions
                        )
                    else:
                        prompt = get_question_generation_prompt(
                            topic, curriculum_context, num_questions,
                            generic_percentage, practical_percentage, difficulty
                        )
                    
                    # Generate questions
                    response = gemini_service.generate_questions(prompt)
                    qa_pairs = gemini_service.parse_qa_pairs(response)
                    
                    # Store in session state
                    st.session_state.qa_pairs = qa_pairs
                    st.session_state.generated_topic = topic
                    
                    st.success(f"✅ Successfully generated {len(qa_pairs)} questions!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating questions: {str(e)}")

# Tab 2: View & Edit Questions
with tab2:
    st.header("📚 View & Edit Questions")
    
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first in the 'Generate Questions' tab")
    else:
        st.success(f"✅ Displaying {len(st.session_state.qa_pairs)} questions for: {st.session_state.generated_topic}")
        
        # Display questions
        for i, qa in enumerate(st.session_state.qa_pairs, 1):
            with st.expander(
                f"Q{i}: {qa['question'][:60]}... [{qa.get('type', 'generic').upper()}]",
                expanded=False
            ):
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.markdown(f"**Type:** {qa.get('type', 'generic').upper()}")
                
                with col2:
                    st.markdown(f"**ID:** {qa['id']}")
                
                st.markdown("### Question")
                edited_question = st.text_area(
                    "Edit question:",
                    value=qa['question'],
                    height=100,
                    key=f"q_{i}"
                )
                
                st.markdown("### Answer")
                edited_answer = st.text_area(
                    "Edit answer:",
                    value=qa['answer'],
                    height=150,
                    key=f"a_{i}"
                )
                
                # Update if edited
                if edited_question != qa['question'] or edited_answer != qa['answer']:
                    st.session_state.qa_pairs[i-1]['question'] = edited_question
                    st.session_state.qa_pairs[i-1]['answer'] = edited_answer
                    st.success("✅ Question updated")

# Tab 3: Export
with tab3:
    st.header("📥 Export Questions")
    
    if st.session_state.qa_pairs is None:
        st.info("💡 Generate questions first in the 'Generate Questions' tab")
    else:
        st.success(f"✅ Ready to export {len(st.session_state.qa_pairs)} questions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_format = st.selectbox(
                "📄 Export Format",
                ["PDF", "Markdown", "Text"]
            )
        
        with col2:
            st.write("")  # Spacer
        
        with col3:
            st.write("")  # Spacer
        
        if export_format == "PDF":
            st.markdown("### PDF Export Settings")
            pdf_title = st.text_input(
                "Document Title",
                value=DOCUMENT_TITLE_FORMAT.format(topic=st.session_state.generated_topic)
            )
            
            if st.button("📥 Download as PDF", use_container_width=True):
                try:
                    pdf_generator = PDFGenerator(
                        pdf_title,
                        st.session_state.generated_topic,
                        "Professional Study Material"
                    )
                    pdf_bytes = pdf_generator.generate(st.session_state.qa_pairs)
                    
                    st.download_button(
                        label="📥 Click to Download PDF",
                        data=pdf_bytes,
                        file_name=f"{pdf_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("✅ PDF generated successfully!")
                except Exception as e:
                    st.error(f"❌ Error generating PDF: {str(e)}")
        
        elif export_format == "Markdown":
            st.markdown("### Markdown Export")
            
            md_content = generate_markdown_document(
                st.session_state.qa_pairs,
                f"Interview Questions - {st.session_state.generated_topic}",
                st.session_state.generated_topic,
                "Professional Study Material"
            )
            
            st.download_button(
                label="📥 Download as Markdown",
                data=md_content,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
            
            # Show preview
            st.markdown("### Preview")
            st.markdown(md_content)
        
        else:  # Text format
            st.markdown("### Text Export")
            
            text_content = ""
            for i, qa in enumerate(st.session_state.qa_pairs, 1):
                text_content += f"QUESTION {i}:\n{qa['question']}\n\n"
                text_content += f"ANSWER {i}:\n{qa['answer']}\n\n"
                text_content += "-" * 80 + "\n\n"
            
            st.download_button(
                label="📥 Download as Text",
                data=text_content,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p style='color: #666;'>🎓 Interview Questions Generator | For Professional Study Materials</p>
    <p style='color: #999; font-size: 12px;'>In collaboration with IIT/IIM courses for working professionals</p>
</div>
""", unsafe_allow_html=True)
