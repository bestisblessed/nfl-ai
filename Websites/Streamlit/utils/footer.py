import streamlit as st

def render_footer(style=1):
    """
    Render a standardized footer for all pages
    
    Args:
        style (int): Footer style number (1-5)
            1: Modern Minimalist
            2: Bold & Colorful
            3: Elegant & Refined
            4: Clean & Spacious
            5: Modern Card Style
    """
    if style == 1:
        render_footer_style_1()
    elif style == 2:
        render_footer_style_2()
    elif style == 3:
        render_footer_style_3()
    elif style == 4:
        render_footer_style_4()
    elif style == 5:
        render_footer_style_5()
    else:
        render_footer_style_1()  # Default to style 1

def render_footer_style_1():
    """Style 1: Modern Minimalist - Clean, simple, with subtle hover effects"""
    st.markdown("""
    <style>
    .footer-style-1 {
        margin-top: 4rem;
        padding: 2.5rem 2rem;
        border-top: 2px solid #e1e8ed;
        background: #ffffff;
    }
    .footer-style-1 .footer-content {
        text-align: center;
        color: #4a5568;
        font-size: 0.9rem;
        line-height: 1.8;
    }
    .footer-style-1 .footer-name {
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
    }
    .footer-style-1 .footer-links {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin: 1rem 0;
    }
    .footer-style-1 .footer-link {
        color: #3182ce;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }
    .footer-style-1 .footer-link:hover {
        color: #2c5282;
        background: #edf2f7;
    }
    .footer-style-1 .footer-copyright {
        margin-top: 1.25rem;
        font-size: 0.85rem;
        color: #a0aec0;
        font-weight: 400;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-style-1">
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

def render_footer_style_2():
    """Style 2: Bold & Colorful - Gradient background with glassmorphism buttons"""
    st.markdown("""
    <style>
    .footer-style-2 {
        margin-top: 4rem;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .footer-style-2 .footer-content {
        text-align: center;
        color: rgba(255, 255, 255, 0.95);
        font-size: 0.95rem;
        line-height: 1.8;
    }
    .footer-style-2 .footer-name {
        font-weight: 800;
        color: white;
        margin-bottom: 1rem;
        font-size: 1.3rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .footer-style-2 .footer-links {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin: 1.25rem 0;
    }
    .footer-style-2 .footer-link {
        color: white;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
        padding: 0.5rem 1rem;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        backdrop-filter: blur(10px);
    }
    .footer-style-2 .footer-link:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .footer-style-2 .footer-copyright {
        margin-top: 1.5rem;
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.8);
        font-weight: 400;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-style-2">
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

def render_footer_style_3():
    """Style 3: Elegant & Refined - Dark theme with animated underline effects"""
    st.markdown("""
    <style>
    .footer-style-3 {
        margin-top: 4rem;
        padding: 3rem 2rem;
        background: #1a202c;
        border-top: 3px solid #667eea;
    }
    .footer-style-3 .footer-content {
        text-align: center;
        color: #cbd5e0;
        font-size: 0.9rem;
        line-height: 1.8;
    }
    .footer-style-3 .footer-name {
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    .footer-style-3 .footer-links {
        display: flex;
        justify-content: center;
        gap: 2.5rem;
        flex-wrap: wrap;
        margin: 1.25rem 0;
    }
    .footer-style-3 .footer-link {
        color: #90cdf4;
        text-decoration: none;
        font-weight: 400;
        transition: all 0.3s ease;
        position: relative;
        padding-bottom: 0.25rem;
    }
    .footer-style-3 .footer-link::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 0;
        height: 2px;
        background: #667eea;
        transition: width 0.3s ease;
    }
    .footer-style-3 .footer-link:hover {
        color: #ffffff;
    }
    .footer-style-3 .footer-link:hover::after {
        width: 100%;
    }
    .footer-style-3 .footer-copyright {
        margin-top: 1.5rem;
        font-size: 0.85rem;
        color: #718096;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-style-3">
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

def render_footer_style_4():
    """Style 4: Clean & Spacious - Light background with bordered link section"""
    st.markdown("""
    <style>
    .footer-style-4 {
        margin-top: 4rem;
        padding: 4rem 2rem;
        background: #f7fafc;
        border-top: 1px solid #e2e8f0;
    }
    .footer-style-4 .footer-content {
        text-align: center;
        color: #4a5568;
        font-size: 0.95rem;
        line-height: 2;
        max-width: 600px;
        margin: 0 auto;
    }
    .footer-style-4 .footer-name {
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1.5rem;
        font-size: 1.15rem;
    }
    .footer-style-4 .footer-links {
        display: flex;
        justify-content: center;
        gap: 3rem;
        flex-wrap: wrap;
        margin: 1.5rem 0;
        padding: 1.5rem 0;
        border-top: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }
    .footer-style-4 .footer-link {
        color: #4299e1;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s ease;
        font-size: 1rem;
    }
    .footer-style-4 .footer-link:hover {
        color: #2b6cb0;
    }
    .footer-style-4 .footer-copyright {
        margin-top: 1.5rem;
        font-size: 0.875rem;
        color: #718096;
        font-weight: 400;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-style-4">
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

def render_footer_style_5():
    """Style 5: Modern Card Style - Elevated card with gradient text and button-style links"""
    st.markdown("""
    <style>
    .footer-style-5 {
        margin-top: 4rem;
        padding: 2.5rem 2rem;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-top: none;
    }
    .footer-style-5 .footer-content {
        text-align: center;
        color: #4a5568;
        font-size: 0.9rem;
        line-height: 1.8;
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        max-width: 700px;
        margin: 0 auto;
    }
    .footer-style-5 .footer-name {
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        display: inline-block;
        padding: 0.5rem 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .footer-style-5 .footer-links {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin: 1.25rem 0;
    }
    .footer-style-5 .footer-link {
        color: #3182ce;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
        padding: 0.5rem 1rem;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        background: white;
    }
    .footer-style-5 .footer-link:hover {
        color: #2c5282;
        border-color: #3182ce;
        background: #ebf8ff;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(49, 130, 206, 0.2);
    }
    .footer-style-5 .footer-copyright {
        margin-top: 1.25rem;
        font-size: 0.85rem;
        color: #718096;
        font-weight: 500;
        padding-top: 1rem;
        border-top: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-style-5">
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
