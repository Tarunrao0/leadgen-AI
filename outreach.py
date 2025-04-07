from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

model = OllamaLLM(model= 'llama3.1')

# Template Library with fallback values
TEMPLATES = {
    "Cold Email (Professional)": {
        "prompt": """Write a professional cold email to {contact} at {company} about {product}. 
        Company details: {details}
        Personalization hook: {hook}
        Max 100 words. Include:
        - Personalized opener
        - 1 relevant statistic
        - Clear CTA""",
        "default_hook": "their recent activity"
    },
    "LinkedIn Connection (Friendly)": {
        "prompt": """Create a friendly LinkedIn connection request mentioning:
        - Common ground (location: {location})
        - How {product} could help
        - Keep under 75 words
        Hook: {hook}""",
        "default_hook": "shared interests",
        "default_location": "your area"
    },
    "Follow-up (Direct)": {
        "prompt": """Write a 3-sentence follow-up:
        1. Reiterate value of {product}
        2. Add urgency
        3. Polite closing
        Hook: {hook}""",
        "default_hook": "our previous discussion"
    }
}

def get_template_options():
    return list(TEMPLATES.keys())

def generate_outreach(template_key, company_data, product, custom_hook=""):
    """Generates message with fallback for missing data"""
    template = TEMPLATES[template_key]
    
    # Prepare variables with fallbacks
    variables = {
        "company": company_data.get("company_name", "their company"),
        "contact": company_data.get("contact_name", "the decision maker"),
        "product": product,
        "details": str(company_data),
        "hook": custom_hook or template.get("default_hook", ""),
        "location": company_data.get("location", template.get("default_location", ""))
    }
    
    # Remove any None values
    variables = {k: v for k, v in variables.items() if v is not None}
    
    prompt = ChatPromptTemplate.from_template(template["prompt"])
    chain = prompt | model  # Your existing OllamaLLM
    
    return chain.invoke(variables)