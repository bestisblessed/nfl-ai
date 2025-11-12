import streamlit as st
from datetime import datetime

def render_footer():
    """Render the footer component."""
    current_year = datetime.now().year
    st.write('##')
    # st.divider()
    st.markdown("""
    <style>
    hr {
        border-color: rgba(0, 0, 0, 0.08) !important;
        opacity: 0.5;
    }
    .footer-design-3 {
        text-align: center;
    }
    .footer-design-3-title {
        font-size: 1rem;
        font-weight: 600;
        color: #474747;
        padding-bottom: 0.3rem;
    }
    .footer-design-3-copyright {
        color: #7f8c8d;
        font-size: 0.8rem;
        font-weight: 400;
    }
    .footer-design-3-copyright-links {
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 1.75rem;
    }
    .footer-design-3-copyright-links a {
        color: #667eea;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.divider()

    st.markdown(f"""
    <div class="footer-design-3">
        <div class="footer-design-3-content">
            <div class="footer-design-3-main">
                <div class="footer-design-3-title">NFL AI © 2023 · Advanced Football Analytics and AI Platform</div>
            </div>
            <div class="footer-design-3-copyright">
                <span class="footer-design-3-copyright-links">
                    <a href="https://github.com/bestisblessed" target="_blank">GitHub</a>
                    <span class="footer-design-3-copyright-separator">|</span>
                    <a href="mailto:tyler.durette@gmail.com">Contact Me</a>
                </span>
                <div style="font-style: italic;" class="footer-design-3-copyright-name">Created by Tyler Durette</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
