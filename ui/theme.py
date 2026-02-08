import streamlit as st


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* 1. Global Font & Sidebar */
        @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;700&display=swap');

        html, body, [class*="st-"] {
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFF9E6, #FFF3CC);
        }

        /* 2. Button Overrides - Fixed Selectors */
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 25px !important;
            padding: 0.5rem 2rem !important;
            font-weight: 700 !important;
            background: linear-gradient(135deg, #FF6B6B, #FF8E8E) !important;
            color: white !important;
            border: none !important;
            transition: all 0.3s ease !important;
            width: auto;
        }

        /* Ensure text inside button is white regardless of Streamlit theme */
        .stButton > button div p, 
        .stButton > button span, 
        .stButton > button div {
            color: white !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #FF8E8E, #FF6B6B) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }

        /* 3. Inputs & Text Areas */
        .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
            border-radius: 15px !important;
            border: 2px solid #FFD93D !important;
        }

        /* 4. Custom Cards & Badges */
        .story-card {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            margin-bottom: 1rem;
            border: 2px solid #FFD93D;
            color: #2D3436;
        }

        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 700;
            color: white;
        }
        
        .status-generating { background: #FFD93D; color: #2D3436; }
        .status-ready { background: #00B894; }

        /* 5. Header & Animations */
        .main-header h1 {
            background: linear-gradient(135deg, #FF6B6B, #FFD93D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            font-weight: 800;
        }

        .typewriter-title {
            display: inline-block;
            overflow: hidden; 
            border-right: 3px solid #FF8C00;
            white-space: nowrap;
            margin: 0 auto;
            animation: 
                typing 1.5s steps(20, end),
                blink-caret .75s step-end infinite;
        }

        @keyframes typing {
            from { width: 0 }
            to { width: 100% }
        }

        @keyframes blink-caret {
            from, to { border-color: transparent }
            50% { border-color: #FF8C00; }
        }
        
        /* Octopus Swimming */
        .header-octopus {
            display: inline-block;
            animation: swim 3s ease-in-out infinite;
            -webkit-text-fill-color: initial; /* Reset gradient for emoji */
        }

        @keyframes swim {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-10px) rotate(5deg); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )