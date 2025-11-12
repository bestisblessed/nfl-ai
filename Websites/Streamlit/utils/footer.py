import streamlit as st

def render_footer(style=1):
    """
    Render a standardized footer for all pages
    
    Args:
        style (int): Footer style number (1-5)
            1: Minimal Line
            2: Compact Gradient
            3: Sleek Dark
            4: Simple Bordered
            5: Clean Inline
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
    """Style 1: Minimal Line - Ultra compact with subtle top border"""
    st.markdown("""
    <style>
    .footer-style-1 {
        margin-top: 3rem;
        padding: 1rem 1rem;
        border-top: 1px solid #e2e8f0;
        background: transparent;
    }
    .footer-style-1 .footer-content {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        line-height: 1.6;
    }
    .footer-style-1 .footer-name {
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .footer-style-1 .footer-links {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        margin: 0.5rem 0;
    }
    .footer-style-1 .footer-link {
        color: #3b82f6;
        text-decoration: none;
        font-weight: 400;
        transition: color 0.2s ease;
    }
    .footer-style-1 .footer-link:hover {
        color: #2563eb;
    }
    .footer-style-1 .footer-copyright {
        margin-top: 0.5rem;
        font-size: 0.75rem;
        color: #94a3b8;
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
    """Style 2: Compact Gradient - Thin gradient bar with compact content"""
    st.markdown("""
    <style>
    .footer-style-2 {
        margin-top: 3rem;
        padding: 1rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .footer-style-2 .footer-content {
        text-align: center;
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.8rem;
        line-height: 1.6;
    }
    .footer-style-2 .footer-name {
        font-weight: 600;
        color: white;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .footer-style-2 .footer-links {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        margin: 0.5rem 0;
    }
    .footer-style-2 .footer-link {
        color: white;
        text-decoration: none;
        font-weight: 400;
        transition: opacity 0.2s ease;
    }
    .footer-style-2 .footer-link:hover {
        opacity: 0.8;
    }
    .footer-style-2 .footer-copyright {
        margin-top: 0.5rem;
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
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
    """Style 3: Sleek Dark - Compact dark footer with minimal styling"""
    st.markdown("""
    <style>
    .footer-style-3 {
        margin-top: 3rem;
        padding: 1rem 1rem;
        background: #1e293b;
        border-top: 1px solid #334155;
    }
    .footer-style-3 .footer-content {
        text-align: center;
        color: #cbd5e1;
        font-size: 0.8rem;
        line-height: 1.6;
    }
    .footer-style-3 .footer-name {
        font-weight: 500;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .footer-style-3 .footer-links {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        margin: 0.5rem 0;
    }
    .footer-style-3 .footer-link {
        color: #94a3b8;
        text-decoration: none;
        font-weight: 400;
        transition: color 0.2s ease;
    }
    .footer-style-3 .footer-link:hover {
        color: #f1f5f9;
    }
    .footer-style-3 .footer-copyright {
        margin-top: 0.5rem;
        font-size: 0.75rem;
        color: #64748b;
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
    """Style 4: Simple Bordered - Clean with subtle border and minimal padding"""
    st.markdown("""
    <style>
    .footer-style-4 {
        margin-top: 3rem;
        padding: 1rem 1rem;
        background: #f8fafc;
        border-top: 1px solid #e2e8f0;
    }
    .footer-style-4 .footer-content {
        text-align: center;
        color: #475569;
        font-size: 0.8rem;
        line-height: 1.6;
    }
    .footer-style-4 .footer-name {
        font-weight: 500;
        color: #1e293b;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .footer-style-4 .footer-links {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        margin: 0.5rem 0;
    }
    .footer-style-4 .footer-link {
        color: #3b82f6;
        text-decoration: none;
        font-weight: 400;
        transition: color 0.2s ease;
    }
    .footer-style-4 .footer-link:hover {
        color: #2563eb;
    }
    .footer-style-4 .footer-copyright {
        margin-top: 0.5rem;
        font-size: 0.75rem;
        color: #94a3b8;
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
    """Style 5: Clean Inline - Single line compact footer"""
    st.markdown("""
    <style>
    .footer-style-5 {
        margin-top: 3rem;
        padding: 0.75rem 1rem;
        border-top: 1px solid #e2e8f0;
        background: transparent;
    }
    .footer-style-5 .footer-content {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        line-height: 1.5;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .footer-style-5 .footer-name {
        font-weight: 500;
        color: #334155;
    }
    .footer-style-5 .footer-separator {
        color: #cbd5e1;
    }
    .footer-style-5 .footer-links {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .footer-style-5 .footer-link {
        color: #3b82f6;
        text-decoration: none;
        font-weight: 400;
        transition: color 0.2s ease;
    }
    .footer-style-5 .footer-link:hover {
        color: #2563eb;
    }
    .footer-style-5 .footer-copyright {
        color: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-style-5">
        <div class="footer-content">
            <span class="footer-name">Tyler Durette</span>
            <span class="footer-separator">•</span>
            <div class="footer-links">
                <a href="https://github.com/bestisblessed" target="_blank" class="footer-link">GitHub</a>
                <a href="mailto:tyler.durette@gmail.com" class="footer-link">Contact Me</a>
            </div>
            <span class="footer-separator">•</span>
            <span class="footer-copyright">NFL AI © 2023</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
