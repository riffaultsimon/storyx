import streamlit as st


def inject_custom_css():
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
            color: #2D3436;
        }

        .stButton > button {
            border-radius: 25px;
            padding: 0.5rem 2rem;
            font-weight: 700;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
            color: white;
            border: none;
            transition: all 0.3s ease;
        }

        .stButton > button p {
            color: white !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #FF8E8E, #FF6B6B);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }

        .stFormSubmitButton > button {
            border-radius: 25px;
            padding: 0.5rem 2rem;
            font-weight: 700;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
            color: white;
            border: none;
            transition: all 0.3s ease;
        }

        .stFormSubmitButton > button p {
            color: white !important;
        }

        .stFormSubmitButton > button:hover {
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
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #FF6B6B;
            box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.2);
        }

        @keyframes storyx-pulse {
            0%, 100% { text-shadow: 0 0 8px rgba(255, 140, 0, 0.4); transform: scale(1); }
            50% { text-shadow: 0 0 24px rgba(255, 140, 0, 0.9), 0 0 48px rgba(255, 107, 107, 0.4); transform: scale(1.08); }
        }

        .storyx-loader {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            padding: 1.5rem 0;
        }

        .storyx-loader .octopus {
            font-size: 3rem;
            animation: storyx-pulse 1.4s ease-in-out infinite;
        }

        .storyx-loader .loader-text {
            color: #636E72;
            font-size: 1rem;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        .seg-badge {
            display: inline-block;
            padding: 0.2rem 0.7rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 700;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
            margin-bottom: 0.25rem;
            color: white;
        }

        .seg-narrator {
            background: #636E72;
        }

        /* --- Animation 1: Swimming Octopus --- */
        @keyframes swim {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            25%      { transform: translateY(-4px) rotate(-5deg); }
            50%      { transform: translateY(0) rotate(0deg); }
            75%      { transform: translateY(2px) rotate(5deg); }
        }

        .header-octopus {
            display: inline-block;
            animation: swim 3s ease-in-out infinite;
            transition: text-shadow 0.3s ease;
            -webkit-text-fill-color: initial;
        }

        /* --- Animation 2: Ink Trail Glow on Hover --- */
        .header-octopus:hover {
            text-shadow: 0 0 12px #FF8C00, 0 0 36px #FF6B6B, 0 0 60px rgba(255, 140, 0, 0.3);
            animation: swim 1.5s ease-in-out infinite;
            cursor: pointer;
            filter: drop-shadow(0 0 8px rgba(255, 140, 0, 0.6));
        }

        /* --- Animation 3: Nav Emoji Bounce --- */
        @keyframes nav-bounce {
            0%, 100% { transform: translateY(0); }
            40%      { transform: translateY(-5px); }
            60%      { transform: translateY(-2px); }
        }

        /* --- Animation 4: Typewriter Title --- */
        @keyframes typewriter-reveal {
            from { clip-path: inset(0 100% 0 0); }
            to   { clip-path: inset(0 0 0 0); }
        }

        @keyframes blink-caret {
            from, to { border-color: transparent; }
            50%      { border-color: #FF8C00; }
        }

        .typewriter-title {
            display: inline-block;
            background: linear-gradient(135deg, #FF6B6B, #FFD93D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            border-right: 3px solid #FF8C00;
            animation: typewriter-reveal 1.5s steps(14, end) both,
                       blink-caret 0.75s step-end 1.5s infinite;
        }

        .typewriter-subtitle {
            opacity: 0;
            animation: fade-in 0.6s ease 1.6s forwards;
        }

        @keyframes fade-in {
            to { opacity: 1; }
        }

        /* --- Footer --- */
        .storyx-footer {
            margin-top: 4rem;
            padding: 1.5rem 1rem;
            border-top: 2px solid #FFD93D;
            text-align: center;
            color: #636E72;
            font-size: 0.75rem;
            line-height: 1.6;
        }

        .storyx-footer .footer-brand {
            font-size: 0.9rem;
            margin-bottom: 0.4rem;
        }

        .storyx-footer a {
            color: #FF8C00;
            text-decoration: none;
            font-weight: 600;
        }

        .storyx-footer a:hover {
            text-decoration: underline;
        }

        .storyx-footer .footer-separator {
            margin: 0 0.3rem;
        }

        /* --- AI Disclosure Badge --- */
        .ai-badge {
            display: inline-block;
            background: linear-gradient(135deg, #74B9FF, #A29BFE);
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
            padding: 0.25rem 0.7rem;
            border-radius: 12px;
            margin-right: 0.4rem;
        }

        .ai-notice {
            background: rgba(116, 185, 255, 0.08);
            border: 1px solid rgba(116, 185, 255, 0.3);
            border-radius: 12px;
            padding: 0.6rem 1rem;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            color: #636E72;
            line-height: 1.5;
        }

        /* --- Landing Page --- */
        .landing-hero {
            text-align: center;
            padding: 3rem 1rem 2rem;
        }

        .landing-features-title {
            text-align: center;
            font-size: 1.4rem;
            font-weight: 700;
            color: #5D4E37;
            margin: 3rem 0 1.5rem;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        .landing-features-title::before,
        .landing-features-title::after {
            content: " — ";
            color: #FFD93D;
        }

        .feature-card {
            background: white;
            border-radius: 20px;
            padding: 2rem 1.5rem;
            text-align: center;
            border: 2px solid #FFD93D;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
        }

        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(255, 140, 0, 0.15);
            border-color: #FF8C00;
        }

        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
        }

        .feature-card-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #2D3436;
            margin-bottom: 0.5rem;
            font-family: 'Bahnschrift', 'Segoe UI', sans-serif;
        }

        .feature-card-desc {
            font-size: 0.9rem;
            color: #636E72;
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
