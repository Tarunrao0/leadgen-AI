from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model= 'llama3.1')

template = (
    "Extract information matching this description: {parse_description}\n\n"
    "Format each finding as:\n"
    "• key:: value\n"
    "• key:: value\n\n"
    "Example for 'extract social media links':\n"
    "• twitter:: https://twitter.com/company\n"
    "• linkedin:: https://linkedin.com/company\n\n"
    "Text to analyze: {dom_content}\n"
    "Return ONLY the key:: value pairs, nothing else."
)

def parse_with_ollama(dom_chunks, parse_description ):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    
    parsed_results = []
    
    for i, chunk in enumerate(dom_chunks, start =1):
        response = chain.invoke({'dom_content': chunk, 'parse_description': parse_description})
        
        print(f"Parsed batch {i} of {len(dom_chunks)}")
        
        parsed_results.append(response)
        
    return '.\n'.join(parsed_results)