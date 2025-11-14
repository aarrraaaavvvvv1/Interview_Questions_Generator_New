import streamlit as st
from modules.gemini_handler import GeminiHandler
from modules.question_generator import QuestionGenerator
from modules.pdf_generator import PDFGenerator
from modules.web_scraper import WebScraper
from app_utils.helpers import sanitize_filename, format_duration
from config import MODEL_CHOICES # Import from config

st.set_page_config(
    page_title="Interview Questions Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- UI helpers ----------

def health_chip(label: str, ok: bool):
    color = "#22c55e" if ok else "#ef4444"
    st.markdown(
        f"<span style='background:{color};padding:2px 8px;border-radius:999px;"
        f"color:white;font-size:12px'>{label}</span>",
        unsafe_allow_html=True
    )

def parse_urls(text: str):
    items = []
    for line in (text or '').splitlines():
        line = line.strip().strip(',')
        if line and (line.startswith('http://') or line.startswith('https://')):
            items.append(line)
    return items

# ---------- Sidebar ----------

def sidebar_form():
    st.sidebar.header("Configuration")

    with st.sidebar.expander("🔑 API Keys (each user enters their own)", expanded=True):
        gemini_key = st.text_input("Gemini API Key*", type="password", placeholder="Paste your Gemini key")
        firecrawl_key = st.text_input("Firecrawl API Key (optional)", type="password", placeholder="Optional")
        # MODEL_CHOICES is now imported from config
        model_name = st.selectbox("Gemini model", MODEL_CHOICES, index=0)
        st.caption("If a model fails, generation will fall back through known variants automatically.")

    topic = st.sidebar.text_input("Main Topic*", placeholder="e.g., Machine Learning")
    subtopics = st.sidebar.text_area("Sub-topics / Context (one per line)", height=100)
    num_questions = st.sidebar.slider("Total Questions", 3, 40, 10, 10)
    generic_pct = st.sidebar.slider("Generic %", 0, 100, 40, 5)
    difficulty = st.sidebar.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    qtypes = st.sidebar.multiselect("Question Types", ["mcq", "coding", "short", "theory"], default=["mcq", "short", "theory"])
    include_answers = st.sidebar.checkbox("Include Answers/Explanations", True)

    urls_text = st.sidebar.text_area(
        "Optional URLs (one per line)",
        placeholder="Leave empty to auto-discover relevant sources",
        height=100
    )

    st.sidebar.markdown("---")
    st.sidebar.write("**Service Status**")

    # Soft, non-blocking validation (for display only)
    gemini_ok = False
    gemini_msg = ""
    if gemini_key:
        try:
            # This probe now performs a real validation
            gh_probe = GeminiHandler(gemini_key, preferred_model=model_name)
            gemini_ok, gemini_msg = gh_probe.validate_api_key_with_reason()
        except Exception as e:
            gemini_ok, gemini_msg = False, str(e)

    health_chip("Gemini", gemini_ok) 
    if not gemini_ok and gemini_key: # Only show error if key is provided but fails
        st.sidebar.caption(f"Gemini probe note: {gemini_msg}")
    elif not gemini_key:
        st.sidebar.caption("Gemini probe note: Awaiting key...")


    health_chip("Firecrawl", bool(firecrawl_key))
    st.sidebar.markdown("---")

    trigger = st.sidebar.button("🎯 Generate Questions", use_container_width=True)

    return dict(
        gemini_key=gemini_key.strip(),
        firecrawl_key=firecrawl_key.strip(),
        model_name=model_name,
        topic=(topic or "").strip(),
        subtopics=[s.strip() for s in (subtopics.splitlines() if subtopics else []) if s.strip()],
        num_questions=num_questions,
        generic_pct=generic_pct,
        difficulty=difficulty,
        qtypes=qtypes,
        include_answers=include_answers,
        urls=parse_urls(urls_text),
        trigger=trigger
    )

# ---------- Renderer ----------

def render_questions(payload: dict):
    st.subheader("🧩 Generated Questions")
    cols = st.columns(4)
    cols[0].metric("Total", payload.get("total_questions", 0))
    cols[1].metric("Generic", payload.get("generic_count", 0))
    cols[2].metric("Practical", payload.get("practical_count", 0))
    cols[3].metric("Time", format_duration(payload.get("generation_time", 0.0)))

    for i, q in enumerate(payload.get("questions", []), start=1):
        with st.expander(f"Q{i}. {q.get('text','(no text)')}", expanded=False):
            st.write(
                f"**Type:** {q.get('type','-')} | **Difficulty:** {q.get('difficulty','-')} | "
                f"{'Generic' if q.get('is_generic') else 'Practical'}"
            )
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

# ---------- Main ----------

def main():
    st.title("🎯 Interview Questions Generator")
    st.caption("Generate realistic interview questions using AI + live web data")

    cfg = sidebar_form()

    if cfg["trigger"]:
        if not cfg["gemini_key"]:
            st.error("Please enter your Gemini API key in the sidebar.")
            st.stop()
        if not cfg["topic"]:
            st.error("Please enter a topic to generate questions.")
            st.stop()

        with st.spinner("Scraping web and generating questions..."):
            # Initialize services with user's keys and preferred model
            gh = GeminiHandler(cfg["gemini_key"], preferred_model=cfg["model_name"])
            qg = QuestionGenerator(gh)
            scraper = WebScraper(cfg["firecrawl_key"])

            # Build context
            context = list(cfg["subtopics"])

            # Scraping: use provided URLs or auto-discover
            scraped = []
            auto_used = False
            try:
                if cfg["urls"]:
                    scraped = scraper.extract_many(cfg["urls"])
                else:
                    query = cfg["topic"] + " " + " ".join(cfg["subtopics"])
                    discovered = scraper.auto_discover_sources(query, max_sources=3)
                    scraped = scraper.extract_many([u for (u, _) in discovered])
                    auto_used = True
            except Exception as e:
                st.warning(f"⚠️ Web scraping issue: {e}")

            if scraped:
                st.info(f"Using {len(scraped)} web source(s){' (auto-discovered)' if auto_used else ''}.")
                for url, text in scraped:
                    snippet = text[:300].replace("\n", " ")
                    context.append(f"[Source] {url} :: {snippet}")

            # Generate questions
            try:
                payload = qg.generate_questions(
                    topic=cfg["topic"],
                    context=context,
                    num_questions=cfg["num_questions"],
                    generic_percentage=cfg["generic_pct"],
                    difficulty_level=cfg["difficulty"],
                    question_types=cfg["qtypes"],
                    include_answers=cfg["include_answers"]
                )
            except Exception as e:
                st.error(f"❌ Gemini generation error: {e}")
                st.stop()

            st.session_state.payload = payload
            render_questions(payload)

    # Export
    payload = st.session_state.get("payload")
    if payload:
        pdf = PDFGenerator()
        fname = sanitize_filename(f"{payload.get('topic','Interview')}_QnA.pdf")
        if st.button("⬇️ Download PDF", use_container_width=True):
            try:
                pdf_path = pdf.generate(payload, filename=fname)
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Save PDF File", f, file_name=fname, mime="application/pdf", use_container_width=True
                    )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    st.markdown("""
    ---
    ### 💡 Tips
    - Each user should enter their **own** Gemini key (separate quotas)
    - Leave URLs empty to auto-discover relevant sources
    - If a model fails, pick another from the dropdown
    """)
    

if __name__ == "__main__":
    main()
