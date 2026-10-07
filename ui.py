"""Shared visual language for the Ballet Technique Analysis Platform."""

import streamlit as st


def inject_app_styles() -> None:
    """Apply the small, global CSS layer needed for a report-style interface."""
    st.markdown(
        """
        <style>
        :root {
            --ivory: #fbf9f6;
            --paper: #ffffff;
            --ink: #24303b;
            --muted: #66717c;
            --navy: #17324d;
            --rose: #9b5d6b;
            --rose-soft: #f3e7e9;
            --line: #dedbd6;
            --strong: #2f7a5b;
            --strong-soft: #e7f3ed;
            --watch: #9a6a16;
            --watch-soft: #fbf1d7;
            --priority: #a64745;
            --priority-soft: #f8e8e6;
            --shadow: 0 12px 30px rgba(31, 43, 54, 0.07);
        }
        .stApp { background: var(--ivory); }
        [data-testid="stHeader"] { background: rgba(251, 249, 246, 0.88); }
        [data-testid="stSidebar"] { background: #f3eee9; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
        [data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 2.25rem; }
        h1, h2, h3 { color: var(--navy); letter-spacing: -0.02em; }
        h1 { font-size: clamp(2rem, 4vw, 3.15rem) !important; line-height: 1.05 !important; }
        h2 { font-size: clamp(1.35rem, 2vw, 1.8rem) !important; }
        h3 { font-size: 1.1rem !important; }
        p, li, label, [data-testid="stCaptionContainer"] { color: var(--ink); }
        [data-testid="stCaptionContainer"] { color: var(--muted); }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line);
            border-radius: 16px;
            box-shadow: var(--shadow);
            background: rgba(255,255,255,.78);
        }
        [data-testid="stMetric"] { padding: .2rem .1rem; }
        [data-testid="stMetricLabel"] { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
        [data-testid="stMetricValue"] { color: var(--navy); font-size: 1.75rem; }
        .eyebrow { color: var(--rose); font-size: .73rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; margin-bottom: .35rem; }
        .lede { color: var(--muted); font-size: 1.06rem; line-height: 1.65; max-width: 760px; }
        .brand-mark { color: var(--navy); font-family: Georgia, serif; font-size: 1.23rem; font-weight: 700; line-height: 1.15; }
        .brand-rule { width: 42px; height: 3px; background: var(--rose); border-radius: 99px; margin: .8rem 0 1rem; }
        .score-panel { background: var(--navy); color: white; border-radius: 16px; padding: 1.3rem 1.45rem; min-height: 150px; }
        .score-panel .score-label { color: #dbe5ec; font-size: .72rem; text-transform: uppercase; letter-spacing: .14em; }
        .score-panel .score { color: white; font: 700 3.25rem/1 Georgia, serif; margin: .35rem 0; }
        .score-panel .score-note { color: #dbe5ec; font-size: .84rem; line-height: 1.45; }
        .report-kicker { color: var(--rose); font-size: .72rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
        .assessment-note { border-left: 3px solid var(--rose); background: var(--rose-soft); border-radius: 0 10px 10px 0; padding: .8rem 1rem; color: var(--ink); }
        .status-chip { display: inline-block; border-radius: 99px; padding: .25rem .6rem; font-size: .75rem; font-weight: 700; }
        .status-chip.strong { color: var(--strong); background: var(--strong-soft); }
        .status-chip.watch { color: var(--watch); background: var(--watch-soft); }
        .status-chip.priority { color: var(--priority); background: var(--priority-soft); }
        .stButton > button, .stLinkButton > a, [data-testid="stFormSubmitButton"] button {
            border-radius: 9px; transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }
        .stButton > button:hover, .stLinkButton > a:hover { transform: translateY(-1px); box-shadow: 0 5px 14px rgba(23,50,77,.12); }
        :focus-visible { outline: 3px solid #c78d9a !important; outline-offset: 2px !important; }
        [data-testid="stFileUploaderDropzone"] { border: 1.5px dashed #bcaab0; background: #fffafa; border-radius: 14px; padding: .8rem; }
        [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--rose); background: #fff7f8; }
        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div style="border-top:1px solid #dedbd6;margin-top:3rem;padding:1.25rem 0 0;color:#66717c;font-size:.78rem;">
            Ballet Technique Analysis Platform · Automated analysis is a training aid and does not replace a qualified instructor.
        </div>
        """,
        unsafe_allow_html=True,
    )
