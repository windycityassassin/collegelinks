import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Base URL of the website
base_url = 'https://www.schoolinks.com'

# Function to get all links from a page
def get_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        # Join the base URL with the link to handle relative URLs
        full_url = urljoin(base_url, a_tag['href'])
        if base_url in full_url:  # Ensure the link is within the same domain
            links.add(full_url)
    return links

# Function to scrape content from a page
def scrape_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else 'No Title'
    text = soup.get_text()
    print(f"Title: {title}\nText: {text[:500]}...\n")  # Print first 500 characters

# Start scraping from the homepage
visited_links = set()
links_to_visit = get_links(base_url)

while links_to_visit:
    link = links_to_visit.pop()
    if link not in visited_links:
        print(f"Scraping {link}")
        scrape_page(link)
        visited_links.add(link)
        # Add new links found on this page
        new_links = get_links(link)
        links_to_visit.update(new_links - visited_links)