import streamlit as st


def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Comic+Neue:wght@400;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Comic Neue', cursive, sans-serif;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Comic Neue', cursive, sans-serif;
            color: #2D3436;
        }

        .stButton > button {
            border-radius: 25px;
            padding: 0.5rem 2rem;
            font-weight: 700;
            font-family: 'Comic Neue', cursive, sans-serif;
            background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
            color: white;
            border: none;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #FF8E8E, #FF6B6B);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }

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

        .status-generating {
            background: #FFD93D;
            color: #2D3436;
        }

        .status-tts_processing {
            background: #74B9FF;
            color: white;
        }

        .status-ready {
            background: #00B894;
            color: white;
        }

        .status-failed {
            background: #FF6B6B;
            color: white;
        }

        .main-header {
            text-align: center;
            padding: 1rem 0;
        }

        .main-header h1 {
            background: linear-gradient(135deg, #FF6B6B, #FFD93D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            margin-bottom: 0;
        }

        .main-header p {
            color: #636E72;
            font-size: 1.1rem;
        }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFF9E6, #FFF3CC);
        }

        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {
            border-radius: 15px;
            border: 2px solid #FFD93D;
            font-family: 'Comic Neue', cursive, sans-serif;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #FF6B6B;
            box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.2);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
