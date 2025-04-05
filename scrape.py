import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import concurrent.futures
import re

def scrape_website(website):
    print("Launching chrome browser...")
    
    chrome_driver_path = ""
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # This is to speed it up a lil
    options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
    options.add_argument("--disable-extensions")
    
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    
    try:
        driver.get(website)
        print("Page Loaded ...")
        html = driver.page_source
        return html
    finally:
        driver.quit()

def scrape_multiple(urls, max_workers=5):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_and_clean, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results.append(future.result())
            except Exception as e:
                results.append({"url": url, "error": str(e)})
    return results

def scrape_and_clean(url):
    """Combined scraping and cleaning for single URL"""
    html = scrape_website(url)
    body = extract_body_content(html)
    cleaned = clean_body_content(body)
    return {
        "url": url,
        "html": html,
        "cleaned_content": cleaned 
    }
     
def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, 'html.parser')
    
    for script_or_style in soup('script', 'style'):
        script_or_style.extract()
        
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())
    
    return cleaned_content

def split_dom_content(dom_content, max_length=6000):
    return [dom_content[i:i + max_length] for i in range(0, len(dom_content), max_length)]

def extract_contact_info(html_content, url):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = list(set(re.findall(email_pattern, text)))
        
        # Extract phone numbers
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phones = list(set(
            ''.join(filter(str.isdigit, phone)) 
            for phone in re.findall(phone_pattern, text)
            if len(''.join(filter(str.isdigit, phone))) >= 7
        ))
        
        # Extract social media links
        social_media = {
            'facebook': [],
            'twitter': [],
            'linkedin': [],
            'instagram': [],
            'youtube': [],
            'pinterest': [],
            'tiktok': [],
            'other': []
        }
        
        social_domains = {
            'facebook.com': 'facebook',
            'twitter.com': 'twitter',
            'linkedin.com': 'linkedin',
            'instagram.com': 'instagram',
            'youtube.com': 'youtube',
            'pinterest.com': 'pinterest',
            'tiktok.com': 'tiktok'
        }
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            
            # Handle relative URLs
            if not href.startswith(('http', 'www')):
                href = urljoin(url, href)
            
            # Check for social media domains
            found = False
            for domain, platform in social_domains.items():
                if domain in href:
                    social_media[platform].append(href)
                    found = True
                    break
            
            if not found and any(platform in href for platform in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'pinterest', 'tiktok']):
                social_media['other'].append(href)
        
        # Deduplicate social media links
        for platform in social_media:
            social_media[platform] = list(set(social_media[platform]))
        
        return {
            'emails': emails,
            'phones': phones,
            'social_media': social_media,
            'source_url': url
        }
    
    except Exception as e:
        return {'error': f"An error occurred: {str(e)}"}