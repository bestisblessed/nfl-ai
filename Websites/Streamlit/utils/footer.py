import streamlit as st

def render_footer():
    """Render a standardized footer for all pages"""
    st.markdown("""
    <style>
    .footer-container {
        margin-top: 60px;
        padding: 30px 20px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-top: 2px solid #dee2e6;
        border-radius: 8px 8px 0 0;
    }
    .footer-content {
        max-width: 1200px;
        margin: 0 auto;
        text-align: center;
    }
    .footer-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    .footer-brand {
        font-size: 1rem;
        font-weight: 700;
        color: #013369;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }
    .footer-links {
        display: flex;
        justify-content: center;
        gap: 24px;
        flex-wrap: wrap;
        margin-top: 12px;
    }
    .footer-link {
        color: #495057;
        text-decoration: none;
        font-size: 0.95rem;
        transition: color 0.3s ease;
        padding: 4px 8px;
    }
    .footer-link:hover {
        color: #013369;
        text-decoration: underline;
    }
    .footer-copyright {
        margin-top: 16px;
        font-size: 0.85rem;
        color: #6c757d;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-container">
        <div class="footer-content">
            <div class="footer-name">Tyler Durette</div>
            <div class="footer-brand">NFL AI © 2023</div>
            <div class="footer-links">
                <a href="https://github.com/bestisblessed" target="_blank" class="footer-link">GitHub</a>
                <a href="mailto:tyler.durette@gmail.com" class="footer-link">Contact Me</a>
            </div>
            <div class="footer-copyright">
                Powered by advanced analytics and machine learning
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
