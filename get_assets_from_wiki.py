import os
import re
import requests

# Constants for paths and URLs
CHARACTERS_FILE_PATH = 'characters.txt'
SCRAPED_IMAGES_DIR = 'img/token/scraped_images/'
BOTC_WIKI_BASE_URL = "https://wiki.bloodontheclocktower.com"

# Ensure the directory for scraped images exists
os.makedirs(SCRAPED_IMAGES_DIR, exist_ok=True)

def read_characters_from_file(file_path):
    """
    Read character names from a file, process, and return a list of characters.
    """
    characters = []
    with open(file_path, 'r') as file:
        for line in file:
            character = line.strip().lower().replace(" ", "").replace("'", "").replace("-", "")
            if character:
                characters.append(character)
    return sorted(characters)

def download_image(image_url, character_name):
    """
    Download and save the image for a character.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        scraped_file = f'{SCRAPED_IMAGES_DIR}{character_name}.png'
        with open(scraped_file, "wb") as file:
            file.write(response.content)
        print(f"Successfully saved {character_name}")
    except requests.HTTPError as e:
        print(f"Failed to download image for {character_name}: {e}")

def scrape_character_images(characters, character_urls):
    """
    Scrape images for characters from the BOTC wiki, with specific URLs for ignored characters.
    """
    for character in characters:
        image_url = character_urls.get(character)
        if image_url:
            print(f"Using provided URL for character: {character}")
            download_image(image_url, character)
        else:
            try:
                url = f"{BOTC_WIKI_BASE_URL}/File:Icon_{character}.png"
                response = requests.get(url)
                response.raise_for_status()  # Raises HTTPError for bad responses

                pattern = r'href="(/images/[^/]+/[^/]+/Icon_[^"]+.png)"'
                matches = re.findall(pattern, response.text)
                if matches:
                    image_url = BOTC_WIKI_BASE_URL + matches[0]
                    download_image(image_url, character)
                else:
                    print(f"No image found for {character}")
            except requests.HTTPError as e:
                print(f"Failed to fetch {character}: {e}")

if __name__ == "__main__":
    # Ignore list with specific URLs
    ignore_list_with_urls = {
        'fortuneteller': 'https://wiki.bloodontheclocktower.com/images/9/97/Icon_fortuneteller.png',
        'harpy': 'https://wiki.bloodontheclocktower.com/images/d/d3/Icon_harpy.png',
        'kazali': 'https://wiki.bloodontheclocktower.com/images/3/3c/Icon_kazali.png',
        'scarletwoman': 'https://wiki.bloodontheclocktower.com/images/1/13/Icon_scarletwoman.png',
    }
    
    characters = read_characters_from_file(CHARACTERS_FILE_PATH)
    scrape_character_images(characters, ignore_list_with_urls)