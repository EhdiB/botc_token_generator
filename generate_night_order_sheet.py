import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image, ImageOps
import os
import tempfile
from pdf2image import convert_from_path

def read_json_values(file_path):
    # Load the JSON data from the file
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Function to recursively extract values from nested JSON
    def extract_values(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                yield from extract_values(value)
        elif isinstance(obj, list):
            for item in obj:
                yield from extract_values(item)
        else:
            yield obj

    # Extract and print all values
    all_values = list(extract_values(data))
    # print("Values in JSON file:", all_values)
    return all_values

def replace_items_with_names(list1, characters_list):
    # Create a dictionary to map 'id' to 'name' from the list of dictionaries
    id_to_name = {character['id']: character['name'] for character in characters_list}

    # Iterate over list1 and replace items using the id_to_name dictionary
    for i, item in enumerate(list1):
        if item.replace('_','') in id_to_name:
            list1[i] = id_to_name[item.replace('_','')]
    return list1



def create_night_sheet(items, characters_json, additional_reminders,additional_reminders_dict):
    # Initialize the new dictionary to store the results
    night_sheet = {}

    # Create a mapping from 'name' to the rest of the dictionary for quick lookup
    character_dict = {character['name']: character for character in characters_json}

    # Loop through each item in the items list
    for item in items:
        if item in character_dict:
            # Access the dictionary corresponding to the current item
            character_info = character_dict[item]
            # Create a new key in night_sheet for this item
            night_sheet[item] = {
                'firstNightReminder': character_info.get('firstNightReminder', ''),
                'otherNightReminder': character_info.get('otherNightReminder', ''),
                'id': character_info.get('id', ''),  # the ID is the item itself
                'image_location': 'img/token/scraped_images/' + character_info.get('id', '') + '.png'
            }
        elif item in additional_reminders:
            # Handle custom reminders for additional items not in characters_json
            night_sheet[item] = additional_reminders_dict[item]

    return night_sheet


def ordered_intersection(list1, list2):
    # Create a set from list1 for faster lookup
    set1 = set(list1)
    # Collect items from list2 that are in list1, preserving the order of list2
    result = [item for item in list2 if item in set1]
    return result



def wrap_text(text, width, font_name, font_size, canvas):
    """
    A utility function to wrap text to fit within a specified width.
    """
    words = text.split()
    wrapped_lines = []
    line = ""
    for word in words:
        test_line = line + word + " "
        if canvas.stringWidth(test_line, font_name, font_size) > width:
            wrapped_lines.append(line)
            line = word + " "
        else:
            line = test_line
    wrapped_lines.append(line)  # add the last line
    return wrapped_lines

def generate_pdf(items, first_other_reminder_key = 'firstNightReminder' ,filename="output.pdf", title="", image_width=100, image_height=100, font_size=12, title_font_size=18):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4    
    h_padding = 30
    v_padding = 5
    v_padding_init = 30
    x_position = h_padding
    y_position = height - v_padding_init  # Start from the top

    # Draw the title
    if title:
        c.setFont("Helvetica-Bold", title_font_size)
        title_width = c.stringWidth(title, "Helvetica-Bold", title_font_size)
        c.drawString((width - title_width) / 2, y_position - title_font_size, title)
        y_position -= (title_font_size * 2)  # Adjust y_position after the title

    temp_files = []  # List to keep track of temporary files

    for key, info in items.items():
        # Load and resize image
        img_path = info['image_location']
        with Image.open(img_path) as img:
            img = img.resize((image_width, image_height))  # Resize method needs adjustment based on Pillow version
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
            img_with_bg = Image.alpha_composite(white_bg, img)
            img_with_bg = img_with_bg.convert('RGB')
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img_with_bg.save(temp_file.name)
            temp_files.append(temp_file.name)

        # Draw image
        image_y_position = y_position - image_height
        c.drawImage(temp_file.name, x_position, image_y_position, width=image_width, height=image_height)

        # Prepare and wrap text
        text_x_position = x_position + image_width #+ h_padding
        text_width = width - text_x_position - 2 * h_padding - 80
        text = f"{info[first_other_reminder_key]}"
        lines = wrap_text(text, text_width, "Helvetica", font_size, c)

        # Calculate text block height
        text_block_height = len(lines) * (font_size * 1.2)
        
        # Text block position and drawing
        text_y_position = image_y_position + font_size 
        c.setFont("Helvetica-Bold", font_size)
        character_width = c.stringWidth(key, "Helvetica-Bold", font_size)
        c.drawString(text_x_position, text_y_position, key)
        c.setFont("Helvetica", font_size)
        for line in lines:
            c.drawString(text_x_position +100, text_y_position, line)
            text_y_position -= font_size * 1.2  # Move up for next line

        # Adjust y_position for next image
        y_position -= max(image_height, text_block_height) + v_padding

        # Check if we need a new page
        if y_position < (image_height + v_padding):
            c.showPage()
            y_position = height - v_padding

    c.save()

    # Cleanup temporary files
    for file_path in temp_files:
        os.remove(file_path)


def convert_pdf_to_image(pdf_path, output_path):
    try:
        # Convert PDF to a list of images (one image per page)
        images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
        
        # Save the first page as an image
        images[0].save(output_path, 'JPEG')
        
        # Remove the PDF file after saving the image
        os.remove(pdf_path)
    except Exception as e:
        print(f"An error occurred: {e}")


def merge_images_side_by_side(image_path1, image_path2, output_path):
    """
    Merges two images side by side and saves the result.

    Parameters:
    - image_path1: Path to the first image file.
    - image_path2: Path to the second image file.
    - output_path: Path to save the merged image.
    """
    # Open the images
    image1 = Image.open(image_path1)
    image2 = Image.open(image_path2)

    # Get the maximum height of the two images
    max_height = max(image1.height, image2.height)

    # Resize images to the maximum height, keeping aspect ratio
    image1 = image1.resize((int(image1.width * max_height / image1.height), max_height))
    image2 = image2.resize((int(image2.width * max_height / image2.height), max_height))

    # Create a new image with a width equal to the sum of both images
    total_width = image1.width + image2.width
    new_image = Image.new('RGB', (total_width, max_height))

    # Paste image1 and image2 next to each other
    new_image.paste(image1, (0, 0))
    new_image.paste(image2, (image1.width, 0))

    # Save the new image
    new_image.save(output_path)




### Start of the main script:

import os

def list_files_in_directory(directory):
    try:
        # List all entries in the directory
        entries = os.listdir(directory)
        
        # Filter out directories, only keep files
        files = [file for file in entries if os.path.isfile(os.path.join(directory, file))]
                # Remove file extensions
        files_without_extensions = [os.path.splitext(file)[0] for file in files]
        
        return files_without_extensions
    except FileNotFoundError:
        print(f"The directory {directory} does not exist.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Specify the directory you want to list files from
script_names = list_files_in_directory('/Users/ehdiburcombe/Documents/BOTC_Tokens_Ehdi/scripts_and_night_order_sheets/scripts')


for script_name in script_names:
    input_script_json=f'scripts_and_night_order_sheets/scripts/{script_name}.json'
    characters_in_script = read_json_values(input_script_json)

    additionnal_reminders = ['DAWN','DUSK','DEMON','MINION']
    characters_in_script_with_reminders = characters_in_script.extend(additionnal_reminders)

    with open('/Users/ehdiburcombe/Documents/BOTC_Tokens_Ehdi/night-order.json', 'r') as file:
            data = json.load(file)
    first_night_order = data['firstNight']
    other_night_order = data['otherNight']

    with open('/Users/ehdiburcombe/Documents/BOTC_Tokens_Ehdi/characters.json', 'r') as file:
            characters_json = json.load(file)

    characters_in_script_clean = replace_items_with_names(characters_in_script, characters_json)
    first_night_order_script = ordered_intersection(characters_in_script_clean,first_night_order)
    other_night_order_script = ordered_intersection(characters_in_script_clean,other_night_order)


    additional_reminders_dict = {'DAWN':{'firstNightReminder': '',
                                        'otherNightReminder': '',
                                        'id': 'dawn',  # Use the item as the ID
                                        'image_location': 'components/dawn.png'},
                                'DUSK':{'firstNightReminder': '',
                                        'otherNightReminder': '',
                                        'id': 'dusk',  # Use the item as the ID
                                        'image_location': 'components/dusk.png'},
                                'DEMON':{'firstNightReminder': 'Wake the Demon, show them their Minions and their Bluffs',
                                        'otherNightReminder': '',
                                        'id': 'dawn',  # Use the item as the ID
                                        'image_location': 'components/demon.png'},
                                'MINION':{'firstNightReminder': 'Wake the Minions, show them the Demon',
                                        'otherNightReminder': '',
                                        'id': 'dawn',  # Use the item as the ID
                                        'image_location': 'components/minion.png'}}

    first_night_sheet = create_night_sheet(first_night_order_script, characters_json, additionnal_reminders, additional_reminders_dict)
    other_night_sheet = create_night_sheet(other_night_order_script, characters_json, additionnal_reminders, additional_reminders_dict)



    # Example usage:
    first_night_file_name = f"scripts_and_night_order_sheets/night_order_sheet/temp/{script_name}order_FirstNight_v2.pdf"
    other_night_filename = f"scripts_and_night_order_sheets/night_order_sheet/temp/{script_name}order_OtherNight_v2.pdf"
    generate_pdf(first_night_sheet, first_other_reminder_key = 'firstNightReminder' , filename=first_night_file_name, title=f"{script_name} - First Night", image_width=30, image_height=30, font_size=10)
    generate_pdf(other_night_sheet, first_other_reminder_key = 'otherNightReminder' , filename=other_night_filename, title=f"{script_name} - Other Nights", image_width=30, image_height=30, font_size=10)

    first_night_image_file_name = f'scripts_and_night_order_sheets/night_order_sheet/temp/{script_name}_first.jpg'
    other_night_image_file_name = f'scripts_and_night_order_sheets/night_order_sheet/temp/{script_name}_other.jpg'
    convert_pdf_to_image(first_night_file_name, first_night_image_file_name)
    convert_pdf_to_image(other_night_filename, other_night_image_file_name)

    output = f'scripts_and_night_order_sheets/night_order_sheet/print/{script_name}_merged.jpg'
    # output = 'merged.jpg'

    # Example usage
    merge_images_side_by_side(first_night_image_file_name, other_night_image_file_name, output)
