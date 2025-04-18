import os
import requests
from bs4 import BeautifulSoup


def find_links(base_url, full_prefix, extensions=None):
    """Fetch all anchor links from a page,
    optionally filtering by file extensions."""
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error accessing {base_url}: {e}")
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


def main():
    base_docs_url = 'https://entscheidsuche.ch/docs/'
    site_root = 'https://entscheidsuche.ch'
    save_dir = '/capstor/store/cscs/swissai/a06/datasets_raw/swiss_data_prep/entscheidsuche.ch/download'  # noqa: E501

    os.makedirs(save_dir, exist_ok=True)

    # Step 1: Find main category links
    raw_links = find_links(base_docs_url, site_root)
    clean_main_links = clean_links(raw_links, site_root)

    # Step 2: From one of those links, get all .pdf and .json files
    all_file_links = []
    for link in clean_main_links:
        files = find_links(link, site_root, extensions=('.pdf', '.json'))
        all_file_links.extend(files)
        break  # remove this if you want to check all folders

    # Step 3: Download files
    for i, file_link in enumerate(all_file_links):
        save_file_from_url(file_link, save_dir)
        if i == 10:
            break


if __name__ == '__main__':
    main()
