import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import concurrent.futures
import re
import time
import requests
from functools import lru_cache

# Add LRU cache for repeated URL scraping
@lru_cache(maxsize=32)
def scrape_website(website, timeout=30):
    print(f"Scraping {website}...")
    
    # Try simple requests first before using Selenium
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(website, headers=headers, timeout=timeout)
        if response.status_code == 200:
            print(f"Successfully scraped {website} using requests")
            return response.text
    except Exception as e:
        print(f"Requests failed for {website}, falling back to Selenium: {str(e)}")
    
    # Fall back to Selenium if requests fails
    print("Launching chrome browser...")
    
    chrome_driver_path = ""
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
    options.add_argument("--disable-extensions")
    options.add_argument("--disk-cache-size=1")
    options.add_argument("--media-cache-size=1")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-offline-load-stale-cache")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--enable-features=NetworkServiceInProcess2")
    
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    driver.set_page_load_timeout(timeout)
    
    try:
        start_time = time.time()
        driver.get(website)
        print(f"Page Loaded in {time.time() - start_time:.2f} seconds")
        html = driver.page_source
        return html
    finally:
        driver.quit()

def scrape_multiple(urls, max_workers=8):
    """Increased max_workers for better parallelization"""
    results = []
    # Remove duplicate URLs
    unique_urls = list(set(urls))
    print(f"Scraping {len(unique_urls)} unique URLs with {max_workers} workers")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_and_clean, url): url for url in unique_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                results.append({"url": url, "error": str(e)})
    return results

def scrape_and_clean(url):
    """Combined scraping and cleaning for single URL"""
    try:
        html = scrape_website(url)
        body = extract_body_content(html)
        cleaned = clean_body_content(body)
        
        # Also extract contact info in the same pass
        contact_info = extract_contact_info(html, url)
        
        return {
            "url": url,
            "html": html,
            "cleaned_content": cleaned,
            "contact_info": contact_info
        }
    except Exception as e:
        print(f"Error in scrape_and_clean for {url}: {str(e)}")
        raise
     
def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Try to find main content areas first
    main_content = soup.find('main') or soup.find(id='content') or soup.find(id='main')
    
    if main_content:
        return str(main_content)
    
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, 'html.parser')
    
    # Remove unnecessary elements
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
        element.extract()
        
    # Remove elements with navigation/menu classes
    for element in soup.find_all(class_=lambda c: c and any(nav_term in c.lower() for nav_term in ['nav', 'menu', 'footer', 'header', 'sidebar'])):
        element.extract()
        
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())
    
    return cleaned_content

def split_dom_content(dom_content, max_length=8000):
    """Increased max_length to reduce number of chunks"""
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
        
        # Only process a limited number of links to improve performance
        for link in soup.find_all('a', href=True, limit=100):
            href = link['href'].lower()
            
            # Only process links that might be social media
            if any(domain in href for domain in social_domains.keys()) or any(platform in href for platform in social_domains.values()):
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
                
                if not found and any(platform in href for platform in social_domains.values()):
                    social_media['other'].append(href)
        
        # Deduplicate social media links
        for platform in social_media:
            social_media[platform] = list(set(social_media[platform]))[:3]  # Limit to top 3 links per platform
        
        return {
            'emails': emails[:5],  # Limit to top 5 emails
            'phones': phones[:3],  # Limit to top 3 phones
            'social_media': social_media,
            'source_url': url
        }
    
    except Exception as e:
        return {'error': f"An error occurred: {str(e)}"}