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
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    }
    .footer-content {
        text-align: center;
        color: #4a5568;
        font-size: 0.9rem;
        line-height: 1.8;
    }
    .footer-name {
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    .footer-links {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        margin-top: 0.75rem;
    }
    .footer-link {
        color: #3182ce;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s ease;
    }
    .footer-link:hover {
        color: #2c5282;
        text-decoration: underline;
    }
    .footer-copyright {
        margin-top: 0.75rem;
        font-size: 0.85rem;
        color: #718096;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-name">Tyler Durette</div>
            <div class="footer-links">
                <a href="https://github.com/bestisblessed" target="_blank" class="footer-link">GitHub</a>
                <a href="mailto:tyler.durette@gmail.com" class="footer-link">Contact Me</a>
            </div>
            <div class="footer-copyright">NFL AI © 2023</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
