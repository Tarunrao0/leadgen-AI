import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re

def scrape_website(website):
    print("Launching chrome browser...")
    
    chrome_driver_path = ""
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options= options)
    
    
    try:
        driver.get(website)
        print("Page Loaded ...")
        
        html = driver.page_source
        
        return html
    
    finally:
        driver.quit()
    
    
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

def split_dom_content(dom_content, max_length = 6000):
    return[
        dom_content[i: i + max_length] for i in range(0, len(dom_content), max_length)
    ]
    
def extract_emails(text):
    email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return list(set(re.findall(email_regex, text)))

def extract_phone_numbers(text):
    """Extract phone numbers (international formats supported)."""
    phone_regex = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    phones = re.findall(phone_regex, text)
    return list(set([re.sub(r"[-.\s()]", "", p) for p in phones if p.strip()]))

def extract_social_links(html_content):
    """
    Extracts social media links (Facebook, Twitter, LinkedIn, Instagram, etc.) from HTML.
    Returns a dictionary with platform names as keys and URLs as values.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    social_links = {}
    
    # Regex patterns for common social media domains
    social_platforms = {
        "facebook": r"https?://(?:www\.)?facebook\.com/[^\s'\"]+",
        "twitter": r"https?://(?:www\.)?twitter\.com/[^\s'\"]+",
        "linkedin": r"https?://(?:www\.)?linkedin\.com/[^\s'\"]+",
        "instagram": r"https?://(?:www\.)?instagram\.com/[^\s'\"]+",
        "youtube": r"https?://(?:www\.)?youtube\.com/[^\s'\"]+",
    }
    
    # Search for <a> tags with href attributes containing social media domains
    for platform, pattern in social_platforms.items():
        links = soup.find_all('a', href=re.compile(pattern, re.IGNORECASE))
        if links:
            # Deduplicate links and add the first one found
            unique_links = list(set(link['href'] for link in links))
            social_links[platform] = unique_links[0]  # Take the first unique link
    
    return social_links

def extract_contact_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    contacts = {
        'emails' : extract_emails(text),
        'phones' : extract_phone_numbers(text),
        'social_links' : extract_social_links(text),
    }
    
    return contacts