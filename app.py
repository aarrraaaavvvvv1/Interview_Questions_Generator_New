import streamlit as st
import os
from modules.gemini_handler import GeminiHandler
from modules.question_generator import QuestionGenerator
from modules.pdf_generator import PDFGenerator
from modules.web_scraper import WebScraper
from app_utils.helpers import sanitize_filename, format_duration


st.set_page_config(
    page_title="Interview Questions Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------- Helper UI Functions ----------

def health_chip(label: str, ok: bool):
    color = "#22c55e" if ok else "#ef4444"
    st.markdown(
        f"<span style='background:{color};padding:2px 8px;border-radius:999px;color:white;font-size:12px'>{label}</span>",
        unsafe_allow_html=True
    )


def parse_urls(text: str):
    items = []
    for line in (text or '').splitlines():
        line = line.strip().strip(',')
        if line and (line.startswith('http://') or line.startswith('https://')):
            items.append(line)
    return items


# ---------- Sidebar Form ----------

def sidebar_form():
    st.sidebar.header("Configuration")

    # API Keys section (per user)
    with st.sidebar.expander("🔑 API Keys (Each user enters their own)"):
        gemini_key = st.text_input(
            "Gemini API Key*", type="password", placeholder="Enter your Gemini API key"
        )
        firecrawl_key = st.text_input(
            "Firecrawl API Key (optional)", type="password", placeholder="Enter your Firecrawl API key"
        )

    topic = st.sidebar.text_input("Main Topic*", placeholder="e.g., Machine Learning")
    subtopics = st.sidebar.text_area(
        "Sub-topics / Context (optional, one per line)", height=100
    )
    num_questions = st.sidebar.slider("Total Questions", 3, 40, 10, 1)
    generic_pct = st.sidebar.slider("Generic %", 0, 100, 40, 5)
    difficulty = st.sidebar.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    qtypes = st.sidebar.multiselect(
        "Question Types", ["mcq", "coding", "short", "theory"],
        default=["mcq", "short", "theory"]
    )
    include_answers = st.sidebar.checkbox("Include Answers/Explanations", True)

    st.sidebar.markdown("---")

    urls_text = st.sidebar.text_area(
        "Optional URLs (one per line)",
        placeholder="Leave empty to let the app find sources automatically",
        height=100
    )

    # API health check
    st.sidebar.markdown("**Service Status**")
    gemini_ok = False
    if gemini_key:
        try:
            gh_probe = GeminiHandler(gemini_key)
            gemini_ok = gh_probe.validate_api_key()
        except Exception:
            gemini_ok = False

    health_chip("Gemini", gemini_ok)
    health_chip("Firecrawl", bool(firecrawl_key))

    st.sidebar.markdown("---")

    # Generate button
    generate_btn = st.sidebar.button("🎯 Generate Questions", use_container_width=True)

    return dict(
        gemini_key=gemini_key.strip(),
        firecrawl_key=firecrawl_key.strip(),
        topic=topic.strip(),
        subtopics=[s.strip() for s in (subtopics.splitlines() if subtopics else []) if s.strip()],
        num_questions=num_questions,
        generic_pct=generic_pct,
        difficulty=difficulty,
        qtypes=qtypes,
        include_answers=include_answers,
        urls=parse_urls(urls_text),
        gemini_ok=gemini_ok,
        trigger=generate_btn
    )


# ---------- Render Questions ----------

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
                f"**Type:** {q.get('type','-')} | **Difficulty:** {q.get('difficulty','-')} | {'Generic' if q.get('is_generic') else 'Practical'}"
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


# ---------- Main App Logic ----------

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
        if not cfg["gemini_ok"]:
            st.error("Your Gemini API key seems invalid or unsupported. Please verify it.")
            st.stop()

        with st.spinner("Scraping web and generating questions..."):
            try:
                # Initialize handlers with user's keys
                gh = GeminiHandler(cfg["gemini_key"])
                qg = QuestionGenerator(gh)
                scraper = WebScraper(cfg["firecrawl_key"])

                # Step 1: Context from subtopics
                context = list(cfg["subtopics"])

                # Step 2: Web scraping
                scraped = []
                if cfg["urls"]:
                    scraped = scraper.extract_many(cfg["urls"])
