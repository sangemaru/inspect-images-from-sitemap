# Importing required libraries
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
from PIL import Image
from io import BytesIO
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# Function to fetch image dimensions with a partial GET request
def fetch_image_dimensions(img_url):
    try:
        # Fetch only the first 100 bytes of the image
        response = requests.get(img_url, headers={'Range': 'bytes=0-100'}, stream=True)
        response.raise_for_status()
        
        # Open the image and get dimensions
        img = Image.open(BytesIO(response.content))
        return f"{img.size[0]}x{img.size[1]}"
    except Exception:
        return "Unknown"

# Function to fetch image details from a given URL
def fetch_images_from_url(url, csvwriter):
    try:
        time.sleep(1)  # Rate limiting: One request per second
        response = requests.get(url)
        response.raise_for_status()
        
        # Check if the content type is HTML before parsing
        if 'text/html' in response.headers.get('Content-Type', ''):
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                print(f"An error occurred while parsing HTML: {e}")
                return
            
            for img in soup.find_all('img'):
                img_url = urljoin(url, img.get('src', ''))
                
                # Skip SVG images
                if img_url.endswith('.svg') or img_url.startswith('data:image/svg+xml'):
                    continue
                
                img_name = img_url.split("/")[-1]  # Filename including extension
                img_format = img_name.split(".")[-1] if '.' in img_name else 'Unknown'
                
                # Fetch image size using a HEAD request
                img_size = 'Unknown'
                try:
                    img_response = requests.head(img_url)
                    img_response.raise_for_status()
                    img_size = img_response.headers.get('content-length', 'Unknown')
                except requests.RequestException:
                    pass
                
                img_resolution = fetch_image_dimensions(img_url)
                csvwriter.writerow([url, img_name, img_url, img_format, img_size, img_resolution])
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

# Main function
def main():
    sitemap_list_file = "sitemap_list.txt"
    output_csv_file = "image_data.csv"
    num_threads = 10

    # Initialize page_urls as an empty list
    page_urls = []

    with open(sitemap_list_file, 'r') as f:
        sitemap_urls = f.read().splitlines()

    # Parse sitemaps to get page URLs
    for sitemap_url in sitemap_urls:
        response = requests.get(sitemap_url)
        soup = BeautifulSoup(response.content, 'xml')
        urls = soup.find_all('loc')
        for url in urls:
            page_urls.append(url.text)
    
    with open('image_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['URL', 'Image Name', 'Image URL', 'Image Format', 'Image Size', 'Image Resolution'])
        
        with ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(lambda url: fetch_images_from_url(url, csvwriter), page_urls), total=len(page_urls)))

if __name__ == '__main__':
    main()
