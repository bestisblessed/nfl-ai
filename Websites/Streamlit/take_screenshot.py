import asyncio
from playwright.async_api import async_playwright
import time
import subprocess
import os

async def take_screenshot():
    # Start Streamlit in the background
    os.chdir('/workspace/Websites/Streamlit')
    env = os.environ.copy()
    env['PATH'] = '/home/ubuntu/.local/bin:' + env.get('PATH', '')
    
    process = subprocess.Popen(
        ['python3', '-m', 'streamlit', 'run', 'Home.py', '--server.headless=true', '--server.port=8501'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    # Wait for server to start and check if it's running
    print("Waiting for Streamlit to start...")
    max_attempts = 15
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
        process.terminate()
        return
    
    time.sleep(3)  # Extra wait for full initialization
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate directly to Team Trends page using the page name
        print("Navigating to Team Trends page...")
        # Streamlit pages are accessible via their filename
        # The page is named "07_📉_Team_Trends.py" so we need to URL encode it
        import urllib.parse
        page_name = urllib.parse.quote('07_📉_Team_Trends')
        url = f'http://localhost:8501/{page_name}'
        print(f"Trying URL: {url}")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f"Direct navigation failed: {e}")
            # Try navigating to home and clicking the link
            await page.goto('http://localhost:8501', wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)
            # Find and click the Team Trends link
            try:
                # Look for link containing Team_Trends or the emoji
                await page.click('text=Team Trends', timeout=5000)
                await page.wait_for_timeout(3000)
            except:
                # Try finding by href
                links = await page.query_selector_all('a')
                for link in links:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and ('Team_Trends' in href or 'Team Trends' in text):
                        await link.click()
                        await page.wait_for_timeout(3000)
                        break
        
        # Wait a bit for charts to load
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        screenshot_path = '/workspace/team_trends_screenshot.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to {screenshot_path}")
        
        await browser.close()
    
    # Kill the Streamlit process
    process.terminate()
    process.wait()

if __name__ == '__main__':
    asyncio.run(take_screenshot())
