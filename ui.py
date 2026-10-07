"""Shared visual language for the minimal, tile-based practice interface."""

import streamlit as st


def inject_app_styles() -> None:
    """Add only presentation CSS; analysis and data handling remain untouched."""
    st.markdown(
        """
        <style>
        :root {
            --canvas: #FFFFFF; --card: #F5F5F5; --card-hover: #EFEFEF;
            --ink: #55534F; --ink-strong: #3F3D3A; --muted: #77746F;
            --line: #E4E2DE; --accent: #66645F; --accent-soft: #ECEBE8;
            --strong: #6F8A6A; --strong-soft: #E8EFE6; --watch: #B98A4A;
            --watch-soft: #F4EBDD; --priority: #9B5A55; --priority-soft: #F4E6E4;
            --focus: #3F3D3A; --shadow: 0 8px 24px rgba(63,61,58,.04);
            --font-display: "Krona One", "Arial Black", sans-serif;
            --font-body: Inter, "Helvetica Neue", Arial, sans-serif;
        }
        * { box-sizing: border-box; }
        .stApp { background: var(--canvas); color: var(--ink); font-family: var(--font-body); }
        [data-testid="stHeader"] { background: rgba(255,255,255,.94); }
        [data-testid="stSidebar"] { background: #FAFAFA; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
        [data-testid="stMainBlockContainer"] { max-width: 1200px; padding: 2.5rem 1.5rem 1rem; }
        h1, h2, h3 { color: var(--ink); font-family: var(--font-display); font-weight: 400; text-transform: lowercase; letter-spacing: -.02em; line-height: 1; }
        h1 { font-size: clamp(2.5rem, 7vw, 5.5rem) !important; }
        h2 { font-size: clamp(1.75rem, 4vw, 3rem) !important; }
        h3 { font-size: clamp(1.1rem, 2vw, 1.5rem) !important; }
        p, li, label, [data-testid="stMarkdownContainer"] { color: var(--ink); }
        [data-testid="stCaptionContainer"] { color: var(--muted); }
        [data-testid="stVerticalBlockBorderWrapper"] { border: 0; border-radius: 24px; box-shadow: none; background: var(--card); padding: .35rem; }
        [data-testid="stMetric"] { padding: .25rem .1rem; }
        [data-testid="stMetricLabel"] { color: var(--muted); font-size: .7rem; text-transform: uppercase; letter-spacing: .14em; }
        [data-testid="stMetricValue"] { color: var(--ink); font-size: 2rem; font-weight: 700; }
        .eyebrow, .report-kicker { color: var(--muted); font-size: .68rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; margin-bottom: .55rem; }
        .eyebrow::before { content: ""; display: inline-block; width: 22px; height: 1px; margin: 0 .65rem .25rem 0; background: var(--muted); }
        .lede { color: var(--muted); font-size: 1.06rem; line-height: 1.65; max-width: 650px; }
        .brand-mark { color: var(--ink-strong); font-family: var(--font-display); font-size: 1.55rem; font-weight: 400; line-height: 1.05; letter-spacing: -.03em; text-transform: lowercase; }
        .brand-rule { width: 42px; height: 2px; background: var(--ink-strong); border-radius: 99px; margin: .9rem 0 1.15rem; }
        .score-panel { position: relative; overflow: hidden; background: var(--card); color: var(--ink); border: 0; border-radius: 24px; padding: 1.5rem; min-height: 150px; box-shadow: none; }
        .score-panel::after { content: ""; position: absolute; left: 1.5rem; bottom: 1.15rem; width: 64px; height: 3px; background: var(--ink-strong); border-radius: 99px; }
        .score-panel .score-label { color: var(--muted); font-size: .68rem; text-transform: uppercase; letter-spacing: .15em; }
        .score-panel .score { color: var(--ink-strong); font: 700 3.5rem/1 var(--font-body); margin: .5rem 0 1.35rem; }
        .score-panel .score-note { color: var(--muted); font-size: .82rem; line-height: 1.45; }
        .assessment-note { border-left: 3px solid var(--ink-strong); background: var(--accent-soft); border-radius: 0 12px 12px 0; padding: .9rem 1rem; color: var(--ink); }
        .status-chip { display: inline-block; border: 1px solid currentColor; border-radius: 999px; padding: .3rem .7rem; font-size: .68rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
        .status-chip.strong { color: var(--strong); background: var(--strong-soft); }
        .status-chip.watch { color: var(--watch); background: var(--watch-soft); }
        .status-chip.priority { color: var(--priority); background: var(--priority-soft); }
        .stButton > button, .stLinkButton > a, [data-testid="stFormSubmitButton"] button { border: 1px solid var(--ink-strong); border-radius: 999px; color: var(--ink-strong); background: transparent; min-height: 2.7rem; padding: .45rem 1.15rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; transition: transform .25s cubic-bezier(.2,.7,.2,1), box-shadow .25s ease, background .25s ease; }
        [data-testid="stFormSubmitButton"] button, .stButton button[kind="primary"] { background: var(--ink-strong); border-color: var(--ink-strong); color: #fff; }
        .stButton > button:hover, .stLinkButton > a:hover { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(63,61,58,.12); background: var(--ink-strong); color: #fff; }
        :focus-visible { outline: 3px solid var(--focus) !important; outline-offset: 3px !important; }
        [data-testid="stFileUploaderDropzone"] { border: 2px dashed #CFCCC6; background: var(--card); border-radius: 24px; padding: 1rem; }
        [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--ink-strong); background: var(--card-hover); }
        [data-testid="stFileUploaderDropzone"] p, [data-testid="stFileUploaderDropzone"] small { color: var(--muted); }
        [data-testid="stProgressBar"] > div > div { background: var(--ink-strong); }
        [data-testid="stVideo"] { border: 0; border-radius: 16px; box-shadow: none; overflow: hidden; }
        [data-testid="stTabs"] button { color: var(--muted); }
        [data-testid="stTabs"] button[aria-selected="true"] { color: var(--ink-strong); border-bottom-color: var(--ink-strong); }
        footer { visibility: hidden; }
        @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; } }
        @media (max-width: 640px) { [data-testid="stMainBlockContainer"] { padding-top: 1.5rem; } h1 { font-size: 2.45rem !important; } [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 20px; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div style="border-top:1px solid #E4E2DE;margin-top:3rem;padding:1.25rem 0 0;color:#77746F;font-size:.78rem;">
            barre · Automated analysis is a practice aid and does not replace a qualified teacher.
        </div>
        """,
        unsafe_allow_html=True,
    )
