import streamlit as st
import pandas as pd
from scrape import scrape_multiple
from parse import parse_with_ollama
from io import StringIO

st.title("🚀 LeadGen AI")

# --- URL Input Section ---
st.subheader("Step 1: Provide URLs")
urls_text = st.text_area(
    "Enter URLs (one per line or comma-separated):",
    height=150,
    placeholder="https://example.com\nhttps://example.org"
)

uploaded_file = st.file_uploader(
    "Or upload CSV (with 'url' column):",
    type=["csv"]
)

# --- Prompt Section ---
st.subheader("Step 2: Define Extraction Prompt")
parse_description = st.text_area(
    "What information should I extract?",
    height=100,
    placeholder="e.g., 'Extract social media links' or 'Get founding year and team size'",
    key="prompt"
)

def parse_urls_input(text_input):
    """Parse URLs from text input"""
    urls = []
    lines = [line.strip() for line in text_input.split('\n') if line.strip()]
    for line in lines:
        urls.extend([url.strip() for url in line.split(',') if url.strip()])
    return urls

def get_urls():
    """Get URLs from either text or CSV"""
    urls = []
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            url_col = 'url' if 'url' in df.columns else df.columns[0]
            urls = df[url_col].dropna().astype(str).tolist()
        except Exception as e:
            st.error(f"CSV Error: {str(e)}")
    if not urls and urls_text:
        urls = parse_urls_input(urls_text)
    return urls

def parse_llm_output(llm_output):
    """Convert LLM's key::value output to dict"""
    result = {}
    for line in llm_output.split('\n'):
        if '::' in line:
            # Handle both • key::value and key::value formats
            clean_line = line.replace('•', '').strip()
            key, value = clean_line.split('::', 1)
            key = key.strip().lower().replace(' ', '_')
            result[key] = value.strip()
    return result

# --- Main Execution ---
urls_to_scrape = get_urls()
if urls_to_scrape:
    st.success(f"URLs to process: {len(urls_to_scrape)}")
    with st.expander("Preview URLs"):
        st.write(urls_to_scrape[:5])

if st.button("Run Extraction") and urls_to_scrape and parse_description:
    all_results = []
    
    with st.spinner(f"Processing {len(urls_to_scrape)} URLs..."):
        scraped_data = scrape_multiple(urls_to_scrape)
        
        for data in scraped_data:
            if 'error' in data:
                all_results.append({"url": data['url'], "error": data['error']})
                continue
            
            try:
                llm_output = parse_with_ollama(
                    dom_chunks=[data['cleaned_content']],
                    parse_description=parse_description
                )
                parsed_data = parse_llm_output(llm_output)
                parsed_data['url'] = data['url']  # Keep source URL
                all_results.append(parsed_data)
            except Exception as e:
                all_results.append({"url": data['url'], "error": str(e)})

    # --- Display Results ---
    if not all_results:
        st.error("No results generated")
        st.stop()
    
    st.subheader("📊 Results Preview")
    df = pd.DataFrame(all_results)
    
    # Move URL to first column
    cols = ['url'] + [c for c in df.columns if c != 'url']
    df = df[cols]
    
    st.dataframe(df.head())
    
    # --- Download ---
    csv = df.to_csv(index=False)
    st.download_button(
        "⬇️ Download as CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
