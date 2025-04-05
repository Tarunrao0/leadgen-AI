import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def extract_contact_info(url):
    try:
        # Fetch the webpage content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all text from the page
        text = soup.get_text()
        
        # Find emails using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = set(re.findall(email_pattern, text))
        
        # Find phone numbers using regex (common formats)
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phones = set(re.findall(phone_pattern, text))
        # Clean phone numbers (remove groups that don't form complete numbers)
        phones = {''.join(filter(str.isdigit, phone)) for phone in phones if len(''.join(filter(str.isdigit, phone))) >= 7}
        
        # Find social media links
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
            'emails': list(emails),
            'phones': list(phones),
            'social_media': social_media,
            'source_url': url
        }
    
    except requests.exceptions.RequestException as e:
        return {'error': f"Failed to fetch URL: {str(e)}"}
    except Exception as e:
        return {'error': f"An error occurred: {str(e)}"}

if __name__ == "__main__":
    website_url = input("Enter the website URL to scrape: ").strip()
    contact_info = extract_contact_info(website_url)
    
    print("\nExtracted Contact Information:")
    print("=" * 50)
    
    if 'error' in contact_info:
        print(contact_info['error'])
    else:
        print("\nEmails found:")
        for email in contact_info['emails']:
            print(f"- {email}")
            
        print("\nPhone numbers found:")
        for phone in contact_info['phones']:
            print(f"- {phone}")
            
        print("\nSocial media links found:")
        for platform, links in contact_info['social_media'].items():
            if links:
                print(f"\n{platform.capitalize()}:")
                for link in links:
                    print(f"- {link}")
    
    print("\n" + "=" * 50)