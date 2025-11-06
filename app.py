import streamlit as st
import os
from config import MODEL_NAME
from modules.gemini_handler import GeminiHandler
from modules.question_generator import QuestionGenerator
from modules.pdf_generator import PDFGenerator
from modules.web_scraper import WebScraper
from app_utils.helpers import sanitize_filename, format_duration

st.set_page_config(page_title="Interview Questions Generator", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

def health_chip(label: str, ok: bool):
    color = "#22c55e" if ok else "#ef4444"
    st.markdown(
        f"<span style='background:{color};padding:2px 8px;border-radius:999px;color:white;font-size:12px'>{label}</span>",
        unsafe_allow_html=True,
    )

def parse_urls(text: str):
    items = []
    for line in (text or '').splitlines():
        line = line.strip().strip(',')
        if line and (line.startswith('http://') or line.startswith('https://')):
            items.append(line)
    return items

def sidebar_form():
    st.sidebar.header("Configuration")

    # API keys (per-user, not from .env)
    with st.sidebar.expander("API Keys (per user)", expanded=True):
        gemini_key = st.text_input("Gemini API Key*", type="password", help="Each user should use their own key.")
        firecrawl_key = st.text_input("Firecrawl API Key (optional)", type="password", help="Improves scraping quality if available.")

    topic = st.sidebar.text_input("Main Topic*", placeholder="e.g., Python Data Structures")
    subtopics = st.sidebar.text_area("Sub-topics / Context (one per line)", height=120)
    num_questions = st.sidebar.slider("Total Questions", 3, 40, 10, 1)
    generic_pct = st.sidebar.slider("Generic %", 0, 100, 40, 5)
    difficulty = st.sidebar.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    qtypes = st.sidebar.multiselect("Question Types", ["mcq", "coding", "short", "theory"], default=["mcq", "short", "theory"])
    include_answers = st.sidebar.checkbox("Include Answers/Explanations", True)

    st.sidebar.markdown("---")
    # Optional: user-supplied URLs. If empty, we will auto-discover sources.
    urls_text = st.sidebar.text_area("Optional URLs (one per line)", height=120)
    st.sidebar.caption("If you leave this empty, the app will automatically discover relevant sources.")

    # Live health chips
    st.sidebar.write("**Services**")
    gemini_ok = False
    if gemini_key:
        try:
            gh_probe = GeminiHandler(gemini_key)
            gemini_ok = gh_probe.validate_api_key()
        except Exception:
            gemini_ok = False
    health_chip("Gemini", gemini_ok)
    health_chip("Firecrawl", bool(firecrawl_key))

    disable_generate = not gemini_ok or not gemini_key or not topic

    if st.sidebar.button("Generate 🎯", type="primary", use_container_width=True, disabled=disable_generate):
        st.session_state._trigger = True

    return dict(
        gemini_key=gemini_key.strip(),
        firecrawl_key=firecrawl_key.strip(),
        topic=(topic or "").strip(),
        subtopics=[s.strip() for s in (subtopics.splitlines() if subtopics else []) if s.strip()],
        num_questions=num_questions,
        generic_pct=generic_pct,
        difficulty=difficulty,
        qtypes=qtypes,
        include_answers=include_answers,
        urls=parse_urls(urls_text),
        gemini_ok=gemini_ok
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

    if st.session_state.get("_trigger"):
        if not cfg["gemini_key"]:
            st.session_state._trigger = False
            st.error("Please enter your Gemini API Key in the sidebar.")
            return

        if not cfg["topic"]:
            st.session_state._trigger = False
            st.error("Please enter a topic.")
            return

        st.session_state._trigger = False
        if not cfg["gemini_ok"]:
            st.error("Your Gemini API key is invalid or the selected model is unavailable. Please check your key or try again.")
            return
        with st.spinner("Scraping web and generating questions..."):
            # Set up services using *per-user* keys
            gh = GeminiHandler(cfg["gemini_key"])
            qg = QuestionGenerator(gh)
            scraper = WebScraper(cfg["firecrawl_key"])

            # 1) Build context
            context = list(cfg["subtopics"])

            # 2) Use user URLs if any; otherwise auto-discover relevant sources
            scraped = []
            if cfg["urls"]:
                scraped = scraper.extract_many(cfg["urls"])
                auto_used = False
            else:
                # auto-discover relevant sources using topic+subtopics
                query = cfg["topic"]
                if cfg["subtopics"]:
                    query += " " + " ".join(cfg["subtopics"])
                discovered = scraper.auto_discover_sources(query=query, max_sources=3)
                scraped = scraper.extract_many([u for (u, _) in discovered]) if discovered else []
                auto_used = True

            # Summarize scraped content into context snippets
            if scraped:
                st.info(f"Using {len(scraped)} web source(s){' (auto-discovered)' if auto_used else ''}.")
                # Add a small snippet per source
                for url, text in scraped:
                    snippet = text[:300].replace("\n", " ")
                    context.append(f"[Source] {url} :: {snippet}")

            # 3) Generate
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
            except exception as e:
                st.error(f"Gemini error: {e}")
                st.stop()
                
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
    **How it works**
    - Enter *your own* Gemini key (each user uses their own quota).
    - Paste URLs if you want; otherwise the app auto-discovers relevant sources.
    - Review questions before sharing with candidates.
    """)

if __name__ == "__main__":
    main()
