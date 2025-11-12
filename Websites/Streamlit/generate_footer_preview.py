from playwright.sync_api import sync_playwright
from PIL import Image
import os

def capture_footer_previews():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1400, "height": 8000})
        
        file_path = os.path.abspath("footer_styles_preview.html")
        page.goto(f"file://{file_path}")
        page.wait_for_load_state("networkidle")
        
        screenshot_path = "footer_styles_preview.png"
        page.screenshot(path=screenshot_path, full_page=True)
        
        browser.close()
        return screenshot_path

if __name__ == "__main__":
    os.chdir("/workspace/Websites/Streamlit")
    screenshot = capture_footer_previews()
    print(f"Screenshot saved to: {screenshot}")
