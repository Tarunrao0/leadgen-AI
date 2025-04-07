import streamlit as st
import pandas as pd
from scrape import scrape_multiple
from parse import parse_with_ollama
from outreach import generate_outreach, get_template_options, TEMPLATES
import pyperclip

# Initialize session state
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = pd.DataFrame()

st.title("🚀 LeadGen AI")

# --- Tab Layout ---
tab1, tab2 = st.tabs(["🔍 Extract Data", "✉️ Create Outreach"])

with tab1:
    # --- URL Input Section ---
    st.header("Step 1: Enter URLs")
    urls_text = st.text_area(
        "Paste URLs (one per line or comma-separated):",
        height=150,
        placeholder="https://example.com\nhttps://example.org"
    )

    uploaded_file = st.file_uploader(
        "Or upload CSV file:",
        type=["csv"]
    )

    # --- Extraction Prompt ---
    st.header("Step 2: What to Extract?")
    parse_prompt = st.text_area(
        "Describe what information you want:",
        height=100,
        placeholder="e.g., 'Extract company name, founding year, and LinkedIn URL'"
    )

    # --- Process URLs ---
    if st.button("Extract Data", type="primary"):
        if not urls_text and not uploaded_file:
            st.warning("Please enter URLs or upload a CSV file")
            st.stop()
        
        if not parse_prompt:
            st.warning("Please specify what to extract")
            st.stop()

        # Get URLs from input
        def parse_urls(text_input):
            urls = []
            lines = [line.strip() for line in text_input.split('\n') if line.strip()]
            for line in lines:
                urls.extend([url.strip() for url in line.split(',') if url.strip()])
            return urls

        urls_to_scrape = []
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                url_col = 'url' if 'url' in df.columns else df.columns[0]
                urls_to_scrape = df[url_col].dropna().astype(str).tolist()
            except Exception as e:
                st.error(f"CSV Error: {str(e)}")
        else:
            urls_to_scrape = parse_urls(urls_text)

        # Scrape and process
        with st.status("Processing URLs...", expanded=True):
            st.write("🔄 Scraping websites...")
            scraped_data = scrape_multiple(urls_to_scrape)
            
            st.write("🔍 Extracting data...")
            results = []
            for data in scraped_data:
                if 'error' in data:
                    results.append({"url": data['url'], "error": data['error']})
                    continue
                
                try:
                    llm_output = parse_with_ollama(
                        dom_chunks=[data['cleaned_content']],
                        parse_description=parse_prompt
                    )
                    
                    # Convert to dict
                    result = {"url": data['url']}
                    for line in llm_output.split('\n'):
                        if '::' in line:
                            key, val = line.split('::', 1)
                            result[key.strip().lower()] = val.strip()
                    results.append(result)
                except Exception as e:
                    results.append({"url": data['url'], "error": str(e)})
            
            st.session_state.leads_df = pd.DataFrame(results)
            st.success("✅ Extraction complete!")

    # --- Show Results ---
    if not st.session_state.leads_df.empty:
        st.header("📊 Extracted Data")
        st.dataframe(st.session_state.leads_df)
        
        # Download
        csv = st.session_state.leads_df.to_csv(index=False)
        st.download_button(
            "Download as CSV",
            data=csv,
            file_name="leads.csv",
            mime="text/csv"
        )

with tab2:
    st.header("Generate Outreach Messages")
    
    if st.session_state.leads_df.empty:
        st.warning("No data found. Extract some leads first!")
        st.stop()
    
    # Template Selection
    selected_template = st.selectbox(
        "Choose a template:",
        options=get_template_options()
    )
    
    # Template Preview
    with st.expander("Template Preview"):
        st.write(TEMPLATES[selected_template]["prompt"])
    
    # Product Info
    product = st.text_input(
        "Your product/service:",
        placeholder="AI-powered CRM for startups"
    )
    
    # Generate Message
    lead_to_message = st.selectbox(
        "Select lead:",
        options=st.session_state.leads_df['url']
    )
    
    if st.button("Generate Message"):
        lead_data = st.session_state.leads_df[
            st.session_state.leads_df['url'] == lead_to_message
        ].iloc[0].to_dict()
        
        message = generate_outreach(
            template_key=selected_template,
            company_data=lead_data,
            product=product
        )
        
        st.text_area("Your Message", message, height=200)
        
        if st.button("Copy to Clipboard"):
            pyperclip.copy(message)
            st.success("Copied!")

# --- Footer ---
st.divider()
st.caption("Tip: Use specific extraction prompts like 'Get CEO emails and recent funding rounds'")