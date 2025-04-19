import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time


def find_links(base_url, full_prefix, extensions=None, max_minutes=10):
    """Fetch all anchor links from a page,
    optionally filtering by file extensions.
    Will timeout after `max_minutes`."""

    start_time = time.time()
    max_seconds = max_minutes * 60

    try:
        # Request with timeout to avoid hanging
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        print(f"⏰ Timeout fetching {base_url}")
        return []
    except requests.RequestException as e:
        print(f"❌ Error accessing {base_url}: {e}")
        return []

    # Check total elapsed time
    if time.time() - start_time > max_seconds:
        print(f"⚠️ Stuck at {base_url} — exceeded {max_minutes} minutes")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = [full_prefix + a['href'] for a in soup.find_all('a', href=True)]

    if extensions:
        links = [link for link in links if link.lower().endswith(extensions)]

    return links


def clean_links(links, base_url):
    """Filter out unwanted links based on custom rules."""
    return [
        link for link in links
        if ('?' not in link)
        and ('.' not in link.split('/')[-1])
        and (link != base_url + '/')
    ]


def save_file_from_url(url, save_dir):
    """Download and save a file from a given URL to a directory."""
    filename = os.path.basename(url)
    filepath = os.path.join(save_dir, filename)

    try:
        response = requests.get(url)
        response.raise_for_status()

        mode = 'w' if filename.endswith('.json') else 'wb'
        content = response.text if mode == 'w' else response.content
        with open(filepath, mode, encoding='utf-8'
                  if mode == 'w' else None) as f:
            f.write(content)

        print(f"✅ Saved: {filename}")
    except requests.RequestException as e:
        print(f"❌ Failed to download {url}: {e}")


import os
from tqdm import tqdm

def main():
    base_docs_url = 'https://entscheidsuche.ch/docs/'
    site_root = 'https://entscheidsuche.ch'
    save_dir = '/capstor/store/cscs/swissai/a06/datasets_raw/swiss_data_prep/entscheidsuche.ch/download'  # noqa: E501
    list_dir = 'list_files.txt'

    os.makedirs(save_dir, exist_ok=True)

    # Step 1: Find main category links
    raw_links = find_links(base_docs_url, site_root)
    clean_main_links = clean_links(raw_links, site_root)

    # Step 2: From one of those links, get all .pdf and .json files
    # if list not present
    if not os.path.exists(list_dir):
        all_file_links = []
        for link in tqdm(clean_main_links, desc="Collecting file links"):
            files = find_links(link, site_root, extensions=('.pdf', '.json'))
            all_file_links.extend(files)

        # save list
        with open(list_dir, 'w') as f:
            for url in all_file_links:
                f.write(f"{url}\n")
    else:
        with open(list_dir, 'r') as f:
            all_file_links = [line.strip() for line in f.readlines()]

    # Step 3: Download files
    for file_link in tqdm(all_file_links, desc="Downloading files"):
        save_file_from_url(file_link, save_dir)



if __name__ == '__main__':
    main()
