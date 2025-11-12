import streamlit as st

def render_footer():
    """Render a standardized footer for all pages"""
    st.divider()
    st.markdown("""
    <style>
    .footer {
        padding: 2rem 1rem;
        margin-top: 3rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-top: 2px solid #dee2e6;
        text-align: center;
    }
    .footer-content {
        max-width: 1200px;
        margin: 0 auto;
    }
    .footer-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .footer-brand {
        font-size: 1rem;
        color: #495057;
        margin-bottom: 1rem;
    }
    .footer-links {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    .footer-link {
        color: #007bff;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.3s ease;
    }
    .footer-link:hover {
        color: #0056b3;
        text-decoration: underline;
    }
    .footer-divider {
        width: 50px;
        height: 2px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        margin: 1rem auto;
        border-radius: 2px;
    }
    </style>
    <div class="footer">
        <div class="footer-content">
            <div class="footer-name">Tyler Durette</div>
            <div class="footer-brand">NFL AI © 2023</div>
            <div class="footer-divider"></div>
            <div class="footer-links">
                <a href="https://github.com/bestisblessed" target="_blank" class="footer-link">GitHub</a>
                <a href="mailto:tyler.durette@gmail.com" class="footer-link">Contact Me</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
