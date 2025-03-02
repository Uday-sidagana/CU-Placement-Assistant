import requests
import os
from dotenv import load_dotenv
from io import BytesIO
from PyPDF2 import PdfReader

# Load API key
load_dotenv()
GEMINI_API = os.getenv("GEMINI_API")

def aiParser(pdf_binary_data):
    pdf_stream = BytesIO(pdf_binary_data)
    pdf_reader = PdfReader(pdf_stream)

    pdf_text = ""
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            pdf_text += text + "\n"

    # Prepare and send request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Analyze the following text and create a structured description:\n\n{pdf_text}"}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)
    response_data = response.json()

    return response_data["candidates"][0]["content"]["parts"][0]["text"]


print(aiParser())
