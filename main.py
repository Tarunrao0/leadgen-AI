import streamlit as st
from scrape import (scrape_website, split_dom_content, clean_body_content, extract_body_content, extract_contact_info) 
from parse import parse_with_ollama

st.title("Leadgen AI")
url = st.text_input("Enter a Website URL: ")

if st.button("Scrape site"):
    st.write("scraping the website")
    
    result = scrape_website(url)
    body_content = extract_body_content(result)
    cleaned_content = clean_body_content(body_content)
    
    contact_info = extract_contact_info(result)
    
    st.session_state.dom_content = cleaned_content
    st.session_state.contact_info = contact_info
    
    with st.expander("View DOM Content"):
        st.text_area("DOM Content", cleaned_content, height=300)
        
    st.subheader("Contact Information")
    
    if contact_info['emails']:
        st.markdown("**Emails:**")
        for email in contact_info['emails']:
            st.code(email)
    else:
        st.warning("No emails found.")
    
    if contact_info["phones"]:
        st.markdown("**📱 Phone Numbers:**")
        for phone in contact_info["phones"]:
            st.code(phone)
    else:
        st.warning("No phone numbers found.")
    
    if contact_info["social_links"]:
        st.markdown("**🌐 Social Media Links:**")
        for platform, url in contact_info["social_links"].items():
            st.markdown(f"- **{platform.capitalize()}**: [{url}]({url})")
    else:
        st.warning("No social media links found.")

    
if "dom_content" in st.session_state:
    parse_description = st.text_area("Describe what you want to parse")
    
    if st.button("Parse Content"):
        if parse_description:
            st.write("Parsing the content")
            
            dom_chunks = split_dom_content(st.session_state.dom_content)
            
            result = parse_with_ollama(dom_chunks, parse_description)
            
            st.write(result)