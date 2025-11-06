import streamlit as st
import os
from dotenv import load_dotenv
from config import MODEL_NAME
from modules.gemini_handler import GeminiHandler
from modules.question_generator import QuestionGenerator
from modules.pdf_generator import PDFGenerator
from modules.web_scraper import WebScraper
from app_utils.helpers import sanitize_filename, format_duration

load_dotenv()
st.set_page_config(page_title="Interview Questions Generator", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

def health_chip(label: str, ok: bool):
    color = "#22c55e" if ok else "#ef4444"
    st.markdown(f"<span style='background:{color};padding:2px 8px;border-radius:999px;color:white;font-size:12px'>{label}</span>", unsafe_allow_html=True)

def parse_urls(text: str):
    items = []
    for line in (text or '').splitlines():
        line = line.strip().strip(',')
        if line and (line.startswith('http://') or line.startswith('https://')):
            items.append(line)
    return items

def sidebar_form():
    st.sidebar.header("Configuration")
    topic = st.sidebar.text_input("Main Topic*", placeholder="e.g., Python Data Structures")
    subtopics = st.sidebar.text_area("Sub-topics / Context (optional, one per line)", height=120)
    num_questions = st.sidebar.slider("Total Questions", 3, 40, 10, 1)
    generic_pct = st.sidebar.slider("Generic %", 0, 100, 40, 5)
    difficulty = st.sidebar.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    qtypes = st.sidebar.multiselect("Question Types", ["mcq","coding","short","theory"], default=["mcq","short","theory"])
    include_answers = st.sidebar.checkbox("Include Answers/Explanations", True)
    st.sidebar.markdown("---")
    use_web = st.sidebar.checkbox("Use Web Scraping (paste URLs below)")
    urls_text = st.sidebar.text_area("URLs (one per line)", height=120, disabled=not use_web)
    st.sidebar.markdown("---")

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")

    # Health chips
    st.sidebar.Write = st.sidebar.write  # silence lints
    st.sidebar.write("**Services**")
    if gemini_key:
        try:
            gh = GeminiHandler(gemini_key)
            ok = gh.validate_api_key()
        except Exception:
            ok = False
    else:
        ok = False
    health_chip("Gemini", ok)
    health_chip("Firecrawl", bool(firecrawl_key))

    if st.sidebar.button("Generate 🎯", type="primary", use_container_width=True):
        st.session_state._trigger = True
    return dict(
        topic=topic.strip() if topic else "",
        subtopics=[s.strip() for s in (subtopics.splitlines() if subtopics else []) if s.strip()],
        num_questions=num_questions,
        generic_pct=generic_pct,
        difficulty=difficulty,
        qtypes=qtypes,
        include_answers=include_answers,
        use_web=use_web,
        urls=parse_urls(urls_text),
        gemini_ok=ok
    )

def render_questions(payload: dict):
    st.subheader("Results")
    cols = st.columns(4)
    cols[0].metric("Total", payload.get("total_questions", 0))
    cols[1].metric("Generic", payload.get("generic_count", 0))
    cols[2].metric("Practical", payload.get("practical_count", 0))
    cols[3].metric("Time", format_duration(payload.get("generation_time", 0.0)))

    for i, q in enumerate(payload.get("questions", []), start=1):
        with st.expander(f"Q{i}. {q.get('text','(no text)')}", expanded=False):
            st.write(f"**Type:** {q.get('type','-')} | **Difficulty:** {q.get('difficulty','-')} | {'Generic' if q.get('is_generic') else 'Practical'}")
            if q.get("type") == "mcq" and isinstance(q.get("options"), list):
                for idx, opt in enumerate(q["options"], start=1):
                    check = "✅ " if opt.get("is_correct") else ""
                    st.write(f"{idx}. {opt.get('option','')}{' ' + check if check else ''}")
                if q.get("explanation"):
                    st.info(f"Explanation: {q.get('explanation')}")
            if q.get("type") == "coding" and q.get("code"):
                st.code(q.get("code"), language="python")
            if q.get("answer") and q.get("type") != "mcq":
                st.success(f"Answer: {q.get('answer')}")
            if q.get("explanation") and q.get("type") != "mcq":
                st.info(f"Explanation: {q.get('explanation')}")

def main():
    st.title("🎯 Interview Questions Generator")
    cfg = sidebar_form()

    if st.session_state.get("_trigger") and cfg["topic"]:
        st.session_state._trigger = False
        with st.spinner("Generating questions..."):
            # Setup services
            gh = GeminiHandler(os.getenv("GEMINI_API_KEY", ""))
            qg = QuestionGenerator(gh)
            scraper = WebScraper(os.getenv("FIRECRAWL_API_KEY", ""))

            # Build context
            context = list(cfg["subtopics"])
            scraped = []
            if cfg["use_web"] and cfg["urls"]:
                scraped = scraper.extract_many(cfg["urls"])
                if scraped:
                    st.info(f"Scraped {len(scraped)} source(s). Adding context from the web.")
                    # append a short snippet per source
                    for url, text in scraped:
                        context.append(f"[Source] {url} :: {text[:300]}")

            # Generate
            payload = qg.generate_questions(
                topic=cfg["topic"],
                context=context,
                num_questions=cfg["num_questions"],
                generic_percentage=cfg["generic_pct"],
                difficulty_level=cfg["difficulty"],
                question_types=cfg["qtypes"],
                include_answers=cfg["include_answers"]
            )
            st.session_state.payload = payload
            render_questions(payload)

    # Export section
    payload = st.session_state.get("payload")
    if payload:
        pdf = PDFGenerator()
        fname = sanitize_filename(f"{payload.get('topic','Interview')}_QnA.pdf")
        if st.button("Download PDF ⬇️", use_container_width=True):
            try:
                pdf_path = pdf.generate(payload, filename=fname)
                with open(pdf_path, "rb") as f:
                    st.download_button("Save PDF file", f, file_name=fname, mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    st.markdown("""
    ---
    **Tips**
    - Provide specific sub-topics for more relevant questions
    - Adjust generic/practical ratio based on your interview focus
    - Paste a handful of authoritative URLs to ground the model with fresh info
    - Review questions before sharing with candidates
    """)


if __name__ == "__main__":
    main()
