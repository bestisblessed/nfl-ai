import asyncio
from playwright.async_api import async_playwright
import time
import subprocess
import os
import base64

async def take_screenshot():
    os.chdir('/workspace/Websites/Streamlit')
    env = os.environ.copy()
    env['PATH'] = '/home/ubuntu/.local/bin:' + env.get('PATH', '')
    
    process = subprocess.Popen(
        ['python3', '-m', 'streamlit', 'run', 'Home.py', '--server.headless=true', '--server.port=8501', '--server.address=0.0.0.0'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    print("Waiting for Streamlit to start...")
    max_attempts = 20
    for i in range(max_attempts):
        try:
            import urllib.request
            urllib.request.urlopen('http://localhost:8501', timeout=2)
            print("Streamlit is running!")
            break
        except:
            print(f"Attempt {i+1}/{max_attempts}: Waiting for server...")
            time.sleep(2)
    else:
        print("Streamlit failed to start")
        stderr_output = process.stderr.read().decode() if process.stderr else "No stderr"
        print(f"Streamlit stderr: {stderr_output[:500]}")
        process.terminate()
        return
    
    time.sleep(5)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("Navigating to Team Trends page...")
        try:
            await page.goto('http://localhost:8501', wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Try to find and click the Team Trends link
            try:
                # Look for the link by text or href
                await page.wait_for_selector('a', timeout=5000)
                links = await page.query_selector_all('a[href*="Team"], a')
                for link in links:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and ('Team_Trends' in href or 'Team Trends' in text or '📉' in text):
                        print(f"Found link: {text} -> {href}")
                        await link.click()
                        await page.wait_for_timeout(5000)
                        break
            except Exception as e:
                print(f"Could not click link: {e}")
                # Try direct URL
                import urllib.parse
                page_name = urllib.parse.quote('07_📉_Team_Trends')
                await page.goto(f'http://localhost:8501/{page_name}', wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Navigation error: {e}")
        
        # Wait for page to fully load
        await page.wait_for_timeout(5000)
        
        # Check for errors on the page
        error_elements = await page.query_selector_all('.stAlert, .error, [class*="error"]')
        if error_elements:
            print(f"Found {len(error_elements)} potential error elements")
            for i, elem in enumerate(error_elements[:3]):
                text = await elem.inner_text()
                print(f"Error element {i+1}: {text[:200]}")
        
        # Take screenshot
        screenshot_path = '/workspace/team_trends_screenshot.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Also get page content to see errors
        page_text = await page.content()
        if 'Error' in page_text or 'error' in page_text.lower():
            print("Page contains error text - checking...")
            # Extract error messages
            error_divs = await page.query_selector_all('div[class*="error"], div[class*="Error"]')
            for div in error_divs[:5]:
                text = await div.inner_text()
                if text:
                    print(f"Error found: {text[:300]}")
        
        await browser.close()
    
    process.terminate()
    process.wait()

if __name__ == '__main__':
    asyncio.run(take_screenshot())
