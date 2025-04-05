from fastapi import FastAPI, Request
from scrape import scrape_website, extract_contact_info, clean_body_content, extract_body_content
from parse import parse_with_ollama

app = FastAPI()

@app.post("/parse")
async def parse_url(request: Request):
    data = await request.json()
    url = data["url"]
    prompt = data.get("prompt", "")  # Column header acts as prompt
    
    # Scrape and clean content
    html = scrape_website(url)
    body = extract_body_content(html)
    cleaned_text = clean_body_content(body)
    
    # If prompt is generic (e.g., "Extract emails"), use contact_info
    if "email" in prompt.lower():
        contacts = extract_contact_info(html)
        return {"result": contacts["emails"]}
    elif "phone" in prompt.lower():
        contacts = extract_contact_info(html)
        return {"result": contacts["phones"]}
    elif "social" in prompt.lower():
        contacts = extract_contact_info(html)
        return {"result": contacts["social_links"]}
    else:
        # Use Llama3 for custom prompts (e.g., "Pricing plans under $50")
        chunks = split_dom_content(cleaned_text)
        parsed = parse_with_ollama(chunks, prompt)
        return {"result": parsed}