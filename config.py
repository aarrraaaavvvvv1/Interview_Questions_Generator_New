import os
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash")
TEMPERATURE = float(os.getenv("GEN_TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("GEN_TOP_P", "0.8"))
MAX_OUTPUT_TOKENS = int(os.getenv("GEN_MAX_OUTPUT_TOKENS", "2048"))
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "20"))
SCRAPE_TOP_K = int(os.getenv("SCRAPE_TOP_K", "3"))
SCRAPE_TRUNCATE_CHARS = int(os.getenv("SCRAPE_TRUNCATE_CHARS", "4000"))
PDF_MARGIN_INCH = float(os.getenv("PDF_MARGIN_INCH", "0.7"))
