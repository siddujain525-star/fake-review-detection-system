import re

def clean_text(text):
    # 1. Handle non-string inputs
    if not isinstance(text, str):
        return ""
    
    # 2. Convert to lowercase
    text = text.lower()
    
    # 3. Remove special characters but KEEP numbers (they matter for ratings/prices!)
    # We remove punctuation but keep the words intact
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # 4. Remove extra whitespace
    text = " ".join(text.split())
    
    return text
