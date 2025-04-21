import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def find_links(base_url, full_prefix, extensions=None):
    """Fetch all anchor links from a page,
    optionally filtering by file extensions."""

    # Request with timeout to avoid hanging
    response = requests.get(base_url)
    response.raise_for_status()

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

        # print(f"✅ Saved: {filename}")
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
    print('Done collecting the main links...')

    # Batch function
    def batch_list(lst, batch_size):
        return [lst[i:i + batch_size] for i in range(0, len(lst), batch_size)]

    # Create batches of main links
    batches = batch_list(clean_main_links, 2)
    print(f"Divided into {len(batches)} batches.")

    # Step 2: From each batch of links, get all .pdf and .json files
    for i, batch in enumerate(tqdm(batches, desc="Collecting batches")):
        print("Processing batch:", batch)

        # Skip batch if all folders exist
        batch_done = True
        for link in batch:
            folder_name = link.split('/')[-2] if link.endswith("/") else link.split('/')[-1]  # noqa: E501
            save_dir_folder = os.path.join(save_dir, folder_name)
            if ((not os.path.exists(save_dir_folder)) or
               (not os.listdir(save_dir_folder))):
                batch_done = False
                break

        if batch_done:
            print(f"Batch {i} already processed. Skipping.")
            continue

        # Process batch
        for link in batch:
            folder_name = link.split('/')[-2] if link.endswith("/") else link.split('/')[-1]  # noqa: E501
            save_dir_folder = os.path.join(save_dir, folder_name)

            os.makedirs(save_dir_folder, exist_ok=True)

            files = find_links(link, site_root, extensions=('.pdf', '.json'))
            for file_link in tqdm(files,
                                  desc=f"Downloading files to {folder_name}"):
                save_file_from_url(file_link, save_dir_folder)

        print('Done with batch number:', i)


if __name__ == '__main__':
    main()
