<p align="center">
    <img src="https://github.com/user-attachments/assets/7d44d1c9-f1d8-477e-8c4c-6485ce086471" alt="banner" height="210" width = "500">
</p>

# LeadGen AI 👾
Leadgen AI is a powerful tool that lets you extract data from any website URL with ease.

# Leadgen AI: How It Works

### Initial Build
Started with a script using Selenium (for dynamic pages) and Beautiful Soup to scrape contact info (emails, phone numbers) and social media links from any URL.

### Data Cleanup
Cleaned and formatted the scraped data, splitting it into chunks to stay within LLM token limits.

### LLM Integration (Llama 3.1)
Chose Llama 3.1 for its speed and cost-efficiency. It analyzes scraped content and generates personalized outreach (cold emails, LinkedIn requests, follow-ups) based on user prompts.

### API & Sheet Integration
Built a FastAPI backend and connected it to Google Sheets via Apps Script for seamless usage.

### Smart Sidebar in Sheets
Integrated a chat sidebar where users can select templates or enter custom prompts—Llama 3.1 handles the messaging instantly.

### Performance

Scraping Accuracy: ~90% (manual testing)

Speed: 2–5s for scraping, 7–10s for responses

Impact: Cuts outreach drafting time by ~70%

# 🚀 How to Run Leadgen AI

### 1. Install Dependencies
Install the required Python libraries:

```bash
pip install -r requirements.txt
```
### 2. Set Up Google Sheets Integration

- Open your Google Sheet

- Go to Extensions → Apps Script

- Open the google-sheets directory from the repo

- Copy and paste the script into the Apps Script editor and save

### 3. Start the API Server

Run the FastAPI server locally:

```bash
uvicorn main:app --reload
```
### 4. Expose Locally with ngrok
Make your local server publicly accessible:

```bash
ngrok http 8000
```
### 5. Use in Google Sheets
Paste URLs into your sheet. Then use the custom formula to extract data:

```excel
=EXTRACT_DATA(urlrange, fieldrange)
```
Example:

```excel
=EXTRACT_DATA(A2:A4, B1:E1)
```
This will scrape the URLs in A2:A4 and return the fields specified in B1:E1.

# Video Demo 
[Youtube 🔗](https://youtu.be/Yqr9LyixnlY)

# Screenshots

Successfully extracted data from Ycombinator's public page

![Image](https://github.com/user-attachments/assets/1dce05c1-a8d8-4e76-9643-ebeab0331bc3)

Generating an outreach mail for collaboration with reddit

![Image](https://github.com/user-attachments/assets/eec045b9-5e72-4de4-a641-678ed7050072)

Output of the outreach mail with the prompt "We are an upcoming social media platform called leadgen"
![Image](https://github.com/user-attachments/assets/197ca511-4c81-45ce-989a-3e41d9edcfd7)

