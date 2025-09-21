import pytesseract
from PIL import Image
import re
import datetime
from openai import OpenAI


def extract_receipt(file_path):
    client = OpenAI()
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    prompt = f"""
    Your goal is to analyze the text and return only a JSON object with the following fields:

    - store_name: string  
    - date: string (YYYY-MM-DD)  
    - items: list of objects {{ "name": string, "quantity": int, "price": float }}  
    - total_amount: float  
    - payment_method: string (if available, else null)  

    Rules:
    1. Always infer the correct values from the text if possible, otherwise return null.  
    2. Normalize item names (e.g., “Hambgr” → “Hamburger”).  
    3. Parse numbers as proper floats or integers, not strings.  
    4. If total is missing, calculate it by summing item prices.  
    5. Return **only valid JSON**, no explanations, no extra text.  


    Extract the structured information from this receipt: {text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts information from receipts."},
            {"role": "user", "content": prompt}
        ]
    )

    structured_text = response.choices[0].message.content

    return text, structured_text