import streamlit as st

def render_footer():
    """Render a standardized footer for all pages"""
    st.markdown("""
    <style>
    .footer {
        margin-top: 4rem;
        padding-top: 2rem;
        padding-bottom: 2rem;
        border-top: 1px solid #e1e8ed;
        background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(248,249,250,1));
    }
    .footer-content {
        text-align: center;
        color: #6c757d;
        font-size: 0.9rem;
        line-height: 1.8;
    }
    .footer-content a {
        color: #3498db;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.3s ease;
    }
    .footer-content a:hover {
        color: #2980b9;
        text-decoration: underline;
    }
    .footer-divider {
        margin: 0 0.5rem;
        color: #dee2e6;
    }
    .footer-brand {
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.5rem;
    }
    .footer-links {
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-brand">NFL AI © 2023</div>
            <div>Tyler Durette</div>
            <div class="footer-links">
                <a href="https://github.com/bestisblessed" target="_blank">GitHub</a>
                <span class="footer-divider">|</span>
                <a href="mailto:tyler.durette@gmail.com">Contact Me</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
