from fastapi import APIRouter, HTTPException
import requests
from bs4 import BeautifulSoup
import re

router = APIRouter()

@router.get("/web/scrape/")
async def scrape_web_content(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract the desired content, e.g., all text
        content = soup.get_text()
        # change any number of consecutive newlines to a single newline
        content = re.sub(r'\n+', '\n', content)
        # change any number of consecutive spaces to a single space
        content = re.sub(r'\s+', ' ', content)
        return {"content": content}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error scraping the web: {str(e)}") 