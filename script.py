import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def fetch_html(url):
    """Fetch the HTML content from the given URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

def extract_links(html_content):
    """Extract theme links from the search result."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []

    # Find the div that contains the search results
    div_search = soup.find('div', class_='div_search')
    
    if div_search:
        for div in div_search.find_all('div', class_='thumbnail_home'):
            a_tag = div.find('a')
            if a_tag and 'href' in a_tag.attrs:
                links.append(a_tag['href'])

    return links

def extract_theme_websites(html_content, theme_name):
    """Extract website names and build download links from the theme page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    websites = []

    # Find the div that contains the website information
    row_div = soup.find('div', class_='row theme_website')
    if row_div:
        for div in row_div.find_all('div', class_='theme_web_div'):
            p_tag = div.find('p', class_='theme_web_h2')
            if p_tag:
                website = p_tag.get_text(strip=True)
                # Create download link using the website name and theme name
                full_link = f"https://{website}/wp-content/themes/{theme_name}.zip"
                websites.append(full_link)

    return websites

def extract_pagination_links(html_content):
    """Extract pagination links from the page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    pagination_links = []

    # Find the pagination div
    pagination_div = soup.find('div', class_='pagination-centered')
    if pagination_div:
        for a_tag in pagination_div.find_all('a', class_='paginator_a'):
            if 'href' in a_tag.attrs:
                pagination_link = a_tag['href']
                if pagination_link not in pagination_links:
                    pagination_links.append(pagination_link)

    return pagination_links

def check_links(links):
    """Check each link and return those that do not return a 404 error."""
    valid_links = []
    
    print("\n" + Fore.CYAN + "_____________________________________")
    print(Fore.YELLOW + "Checking links for ...\n")
    
    for link in links:
        try:
            response = requests.head(link, allow_redirects=True)
            if response.status_code != 404:
                valid_links.append(link)
                print(Fore.GREEN + f"Valid link: {link}")
        except requests.RequestException:
            continue  # Skip links that cause exceptions without printing errors
    
    return valid_links

def download_file(url):
    """Download the file from the given URL and rename it based on the domain."""
    local_filename = url.split('/')[-1]
    
    # Extract the domain from the URL
    domain = urlparse(url).netloc
    
    # Create the new filename with the domain included
    name, ext = os.path.splitext(local_filename)
    new_filename = f"{name}[{domain}]{ext}"
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(new_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        print(Fore.GREEN + f"Successfully downloaded: {new_filename}")
    except requests.HTTPError:
        print(Fore.RED + f"Failed to download: {url}")
        return False
    return True

if __name__ == "__main__":
    print(Fore.CYAN + "Welcome to the Theme Link Checker!")
    print("Please enter the name of the theme you want to search for.\n")
    
    theme_name = input("Enter the theme name: ")
    search_url = f"https://themesinfo.com/?search_type=anywhere&search={theme_name}&s=1"
    
    print(Fore.YELLOW + "Please wait, it may take some time. Thank you for your patience.")
    
    # Fetch the initial HTML content from the search results
    html_content = fetch_html(search_url)
    
    if html_content:
        # Extract links from the search results
        links = extract_links(html_content)

        # Download the content from the first link
        if links:
            first_link = links[0]
            print(Fore.YELLOW + f"Fetching data from: {first_link}...")
            time.sleep(1)  # Simulating loading time
            page_content = fetch_html(first_link)
            if page_content:
                # Extract website names from the downloaded content
                all_websites = extract_theme_websites(page_content, theme_name)

                # Show a message after the first link is processed
                print(Fore.YELLOW + f"Processed the first theme link. Found {len(all_websites)} websites.")
                
                # Check for pagination links and download content from those pages
                pagination_links = extract_pagination_links(page_content)
                visited_links = set()  # To track visited pagination links

                for pagination_link in pagination_links:
                    if pagination_link not in visited_links:
                        visited_links.add(pagination_link)
                        print(Fore.YELLOW + f"Fetching data from pagination: {pagination_link}...")
                        time.sleep(1)  # Simulating loading time
                        next_page_content = fetch_html(pagination_link)
                        if next_page_content:
                            websites = extract_theme_websites(next_page_content, theme_name)
                            all_websites.extend(websites)
                            print(Fore.YELLOW + f"Found {len(websites)} additional websites on this page.")

                # Check the extracted links for 404 errors
                valid_links = check_links(all_websites)

                # Ask the user if they want to download the valid files
                if valid_links:
                    download_choice = input(Fore.YELLOW + "\nDo you want to download the valid files? (yes/no): ").strip().lower()
                    if download_choice in ['yes', 'y']:
                        for valid_link in valid_links:
                            download_file(valid_link)
                else:
                    print(Fore.RED + "No valid links found for downloading.")
            else:
                print(Fore.RED + "Failed to download content from the first link.")
        else:
            print(Fore.RED + "No links found in the search results.")
    else:
        print(Fore.RED + "Failed to fetch HTML content.")
