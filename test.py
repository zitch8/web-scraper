from bs4 import BeautifulSoup
import requests

def test_beautifulsoup():
    url = "https://philnews.ph/2025/08/18/4d-lotto-result-today-monday-august-18-2025"

    # Simulate fetching the HTML content (in practice, use requests or similar library)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure we got a successful response
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e: 
        print(f"Error fetching the URL: {e}")
        return
    
print(test_beautifulsoup())