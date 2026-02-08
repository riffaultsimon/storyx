import streamlit as st

def inject_custom_css():
    st.markdown(
        """
        <style>
        /* --- 1. GLOBAL & FONT SETUP --- */
        html, body, [class*="st-"] {
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
            color: #2D3436;
        }

        /* --- 2. SIDEBAR & INPUTS --- */
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFF9E6, #FFF3CC);
        }

        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {
            border-radius: 15px;
            border: 2px solid #FFD93D;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #FF6B6B;
            box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.2);
        }

        /* --- 3. MAIN ACTION BUTTONS (Pink Gradient) --- */
        /* Targets all buttons EXCEPT those inside the footer container */
        div:not([data-testid="stHeader"]) div[data-testid="column"]:not([data-testid="footer_links"]) .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 25px !important;
            padding: 0.5rem 2rem !important;
            font-weight: 700 !important;
            background: linear-gradient(135deg, #FF6B6B, #FF8E8E) !important;
            color: white !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }

        /* Force text inside main buttons to be white */
        div:not([data-testid="footer_links"]) .stButton > button p,
        div:not([data-testid="footer_links"]) .stButton > button span {
            color: white !important;
        }

        div:not([data-testid="footer_links"]) .stButton > button:hover {
            background: linear-gradient(135deg, #FF8E8E, #FF6B6B) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }

        /* --- 4. STORY CARDS & BADGES --- */
        .story-card {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            margin-bottom: 1rem;
            border: 2px solid #FFD93D;
        }

        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 700;
        }

        .status-generating { background: #FFD93D; color: #2D3436; }
        .status-tts_processing { background: #74B9FF; color: white; }
        .status-ready { background: #00B894; color: white; }
        .status-failed { background: #FF6B6B; color: white; }

        /* --- 5. ANIMATED HEADER & OCTOPUS --- */
        .main-header { text-align: center; padding: 1rem 0; }
        
        .typewriter-title {
            display: inline-block;
            background: linear-gradient(135deg, #FF6B6B, #FFD93D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            border-right: 3px solid #FF8C00;
            animation: typewriter-reveal 1.5s steps(14, end) both,
                       blink-caret 0.75s step-end infinite;
        }

        @keyframes typewriter-reveal {
            from { clip-path: inset(0 100% 0 0); }
            to { clip-path: inset(0 0 0 0); }
        }

        @keyframes blink-caret {
            from, to { border-color: transparent; }
            50% { border-color: #FF8C00; }
        }

        @keyframes swim {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-5px) rotate(2deg); }
        }

        .header-octopus {
            display: inline-block;
            animation: swim 3s ease-in-out infinite;
            -webkit-text-fill-color: initial; /* Essential to keep emoji colors */
        }

        /* --- 6. FOOTER STYLING --- */
        .storyx-footer {
            margin-top: 4rem;
            padding: 1.5rem 1rem;
            border-top: 2px solid #FFD93D;
            text-align: center;
            color: #636E72;
            font-size: 0.75rem;
            line-height: 1.6;
        }

        .ai-notice {
            background: rgba(116, 185, 255, 0.08);
            border: 1px solid rgba(116, 185, 255, 0.3);
            border-radius: 12px;
            padding: 0.6rem 1rem;
            margin: 0.5rem auto;
            max-width: 80%;
            font-size: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )