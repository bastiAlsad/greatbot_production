import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
import time
import re

def get_all_links(url, base_domain):
    """Crawl a given URL and return all links within the same base domain."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except (requests.RequestException, ValueError) as e:
        print(f"Error fetching {url}: {e}")
        return set()  # Return an empty set on error

    links = set()
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        full_url = urljoin(url, href)
        parsed_url = urlparse(full_url)
        extracted = tldextract.extract(parsed_url.netloc)
        if f"{extracted.domain}.{extracted.suffix}" == base_domain:
            links.add(full_url)

    return links

def clean_text(text):
    """Remove non-informative and binary data from text."""
    # Remove non-printable characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text_from_url(url):
    """Extract all text content from a given URL, filtering out media and scripts."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove non-text elements
        for tag in soup(['script', 'style', 'img', 'video', 'audio']):
            tag.decompose()

        # Extract text from typical content elements
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div'])
        texts = [element.get_text(strip=True) for element in text_elements]
        
        full_text = '\n'.join(texts)
        return clean_text(full_text)
    except (requests.RequestException, ValueError) as e:
        print(f"Error fetching {url}: {e}")
        return ""

def crawl_and_extract(base_url, delay=1, max_pages=100):
    """Crawl all subdomains of the base URL and extract their text content."""
    parsed_base_url = urlparse(base_url)
    base_domain = f"{tldextract.extract(parsed_base_url.netloc).domain}.{tldextract.extract(parsed_base_url.netloc).suffix}"
    
    to_visit = {base_url}
    visited = set()
    all_texts = []
    page_count = 0

    while to_visit and page_count < max_pages:
        current_url = to_visit.pop()
        if current_url in visited:
            continue
        visited.add(current_url)
        print(f"Visiting: {current_url}")
        
        all_texts.append(extract_text_from_url(current_url))
        links = get_all_links(current_url, base_domain)
        to_visit.update(links - visited)
        
        page_count += 1
        #time.sleep(delay)  # Add delay to reduce server load

    return "\n\n".join(all_texts)

def save_text_to_file(text, file_path):
    """Save the extracted text to a .txt file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)

def crawl_website(url, company_name):#
    base_url = url
    output_file = f'customer_files/{company_name}.txt'
    print("Crawling and extracting text, please wait...")
    all_texts = crawl_and_extract(base_url)
    save_text_to_file(all_texts, output_file)
    print(f"Text extracted and saved to {output_file}")


# crawl_website()