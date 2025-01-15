import os
import json
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from PIL import Image, ImageDraw
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image as wandImage
import math


# Constants for file paths and configuration
IMG_TOKEN_PATH = 'img/token'
SCRAPED_IMAGES_PATH = os.path.join(IMG_TOKEN_PATH, 'scraped_images')
GENERATED_TOKENS_PATH = os.path.join(IMG_TOKEN_PATH, 'generated_tokens')
GENERATED_REMINDERS_PATH = os.path.join(IMG_TOKEN_PATH, 'generated_reminders')
CURVED_CHARACTER_NAMES_PATH = os.path.join(IMG_TOKEN_PATH, 'curved_character_names')
CURVED_REMINDERS_PATH = os.path.join(IMG_TOKEN_PATH, 'curved_reminders')
CHARACTERS_JSON_PATH =  'characters.json'
TOKEN_BG_PATH = 'img/token_bg'

# Ensure all necessary directories exist
for path in [SCRAPED_IMAGES_PATH, GENERATED_TOKENS_PATH, GENERATED_REMINDERS_PATH, CURVED_CHARACTER_NAMES_PATH, CURVED_REMINDERS_PATH]:
    os.makedirs(path, exist_ok=True)

def get_filenames_no_extension(folder_path):
    """
    Returns a list of filenames without their extension in a given folder.
    """
    return [
        os.path.splitext(file)[0] for file in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, file)) and file != '.DS_Store'
    ]

def plot_curved_text(text, radius=90, filename='curved_text.png', start_angle=270, margin=10, text_color='Black'):
    """
    Plots curved text around a circle with specified parameters.
    """
    fig, ax = plt.subplots()
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    ax.set_xlim(-radius-margin, radius+margin)
    ax.set_ylim(-radius-margin, radius+margin)

    max_spread, max_len_text = 150, 19
    spread = (len(text)/max_len_text) * max_spread
    for i, char in enumerate(text):
        start_angle_relative = start_angle - (spread/2 - spread / len(text)/2)
        angle = start_angle_relative + spread * i/ len(text)
        x = radius * np.cos(np.radians(angle))
        y = radius * np.sin(np.radians(angle))
        rotation = angle + 90
        font = FontProperties(family='monospace', weight='bold', size=30)
        ax.text(x, y, char, color=text_color, ha='center', va='bottom', rotation=rotation, fontproperties=font)
    ax.axis('off')
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, dpi=300, transparent=True)
    plt.close(fig)


def curved_text_to_image(text, filepath='curved_text.png', token_diameter = 500):
    """Change a text string into an image with curved text.

    Args:
        text (str): The text to be displayed.
        token_type (str): The type of text to be displayed. Either "reminder" or "role".
        token_diameter (int): The width of the token. This is used to determine the amount of curvature.
        components (TokenComponents): The component package to load fonts from.
    """
    # Make sure we have text to draw. Otherwise, just return an empty image.
    img = wandImage(width=1, height=1, resolution=(600, 600))
    if text == "":
        return img

    # Set up the font and color based on the token type
    token_diameter = int(token_diameter - (token_diameter * 0.1))  # Reduce the diameter by 10% to give a little padding
    font_size = token_diameter * 0.15 
    font_filepath = 'components/RoleName.ttf'
    color = "#000000"
    text = text.upper()

    # Create the image
    with Drawing() as draw:
        # Assign font details
        draw.font = font_filepath
        draw.font_size = font_size
        draw.fill_color = Color(color)
        # Get size of text
        height, width = 0, math.inf
        # Downsize the text until it fits within the token
        while True:
            metrics = draw.get_font_metrics(img, text)
            height, width = int(metrics.text_height), int(metrics.text_width)
            if width > 2 * token_diameter * 0.5:
                draw.font_size = draw.font_size * 0.95
            else:
                break

        # Resize the image
        img.resize(width=width, height=int(height * 1.2))
        # Draw the text
        draw.text(0, height, text)
        draw(img)
        img.virtual_pixel = 'transparent'
        # Curve the text
        # The curve angle can be found by treating the text width as a chord length and the token width as the diameter
        # By bisecting this chord we can create a right triangle and solve for the angle.
        # If the text width is greater than the token width, the angle will be greater than 180 degrees.
        additional_curve = 0
        if width > token_diameter:
            width = width - token_diameter
            additional_curve = 180
        curve_degree = round(math.degrees(2 * math.asin((width / 2) / (token_diameter / 2)))) + additional_curve
        # rotate it 180 degrees since we want it to curve down, then distort and rotate back 180 degrees
        img.rotate(180)
        img.distort('arc', (curve_degree, 180))
        img_width = img.width

        img.save(filename=filepath)

        # Create a transparent base image of the new size
        square_size = 500

    with wandImage(width=square_size , height=square_size  , background=Color('transparent')) as base_image:
        # Load the original image
        with wandImage(filename=filepath) as original_image:
            # Composite the original image over the transparent base
            # positioned at the bottom of the base image
            padding_top = int(square_size*0.92 - img.height)
            padding_left = int((square_size - img_width)/2)
            base_image.composite(original_image, left=padding_left, top=padding_top)
            
            # Save the result
            base_image.save(filename=filepath)


def generate_overlay_array(character_data, folder_path, is_reminder=False, reminder=''):
    """
    Generates an array of image paths for overlay, based on character data and conditions.
    """
    overlay_array = ['img/token_bg/clockface-2-very_white.png'] if is_reminder else []
    curved_text_subpath = CURVED_REMINDERS_PATH if is_reminder else CURVED_CHARACTER_NAMES_PATH
    curved_text_filename = f"{character_data['id']}_{reminder}.png" if is_reminder else f"{character_data['id']}.png"
    curved_text_path = os.path.join(curved_text_subpath, curved_text_filename)

    if not is_reminder:
        reminder_count = len(character_data['reminders'])
        if 1 <= reminder_count <= 6:  # Assuming overlays for 1 to 6 reminders exist
            overlay_array.append(f'img/token/leaves/top-{reminder_count}.png')
        if character_data['firstNight'] != 0:
            overlay_array.append('img/token/leaves/left-1.png')
        if character_data['otherNight'] != 0:
            overlay_array.append('img/token/leaves/right-1.png')
        if character_data.get('setup', False):
            overlay_array.append('img/token/leaves/setup.png')

    overlay_array.append(os.path.join(folder_path, f"{character_data['id']}.png"))
    overlay_array.append(curved_text_path)
    return overlay_array


# Define a single function for overlay with alpha composite
def overlay_with_alpha_composite(base_image_path, overlay_image_paths, output_path, mask_color):
    """
    Applies one or more overlay images on top of a base image and saves the result.
    Optionally adds a transparent mask to the composite image.
    
    Args:
    - base_image_path (str): The path to the base image.
    - overlay_image_paths (list[str]): A list of paths to overlay images.
    - output_path (str): The path where the final composite image will be saved.
    - add_transparent_mask (bool): If True, adds a circular transparent mask to the composite.
    """
    try:
        base_img = Image.open(base_image_path).convert("RGBA")

        for overlay_image_path in overlay_image_paths:
            overlay_img = Image.open(overlay_image_path).convert("RGBA")
            overlay_img_resized = overlay_img.resize(base_img.size, Image.Resampling.LANCZOS)
            base_img = Image.alpha_composite(base_img, overlay_img_resized)


        # Apply a transparent mask if requested
        width, height = base_img.size
        colored_bg_img = Image.new('RGBA', (width, height), mask_color)
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, height), fill=255)
        base_img = Image.composite(base_img, colored_bg_img, mask)

        base_img.save(output_path)

    except Exception as e:
        print(f"An error occurred: {e}")

# Main processing logic

if __name__ == "__main__":
    try:
        with open(CHARACTERS_JSON_PATH, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: '{CHARACTERS_JSON_PATH}' not found.")
        exit()

    characters_in_json = [character['id'] for character in data]
    character_names = get_filenames_no_extension(SCRAPED_IMAGES_PATH)


    # Identify missing characters in the JSON file
    missing_characters_in_json = [item for item in character_names if item not in characters_in_json]
    if missing_characters_in_json:
        print("These characters are not in the JSON and will not be generated:", missing_characters_in_json)

    for character in data:
        if character['id'] in character_names:
        # if character['id'] in ['devilsadvocate','drunk','po']:
            try:
                # if character['edition'] == 'tb':
                    # Process big character tokens
                curved_character_names_path = os.path.join(CURVED_CHARACTER_NAMES_PATH, f"{character['id']}.png")
                curved_text_to_image(character['name'].upper(), filepath=curved_character_names_path, token_diameter=500)

                leaf_array = generate_overlay_array(character, SCRAPED_IMAGES_PATH)
                result_image_path = os.path.join(GENERATED_TOKENS_PATH, f"{character['id']}.png")
                overlay_with_alpha_composite(os.path.join(TOKEN_BG_PATH, 'official_assets/token.b01ebc0e.png' ), leaf_array, result_image_path, mask_color=(86, 68, 46, 0))
                print(f'{character["id"]} - Token created successfully!')
                
                # Process small reminder tokens
                for reminder in character['reminders']:
                    curved_reminders_path = os.path.join(CURVED_REMINDERS_PATH, f"{character['id']}_{reminder}.png")
                    plot_curved_text(reminder, radius=130, filename=curved_reminders_path, start_angle=270, margin=10, text_color = 'White')

                    leaf_array_reminder = generate_overlay_array(character, SCRAPED_IMAGES_PATH, is_reminder=True, reminder=reminder)
                    result_image_reminder_path = os.path.join(GENERATED_REMINDERS_PATH, f"{character['id']}_{reminder}.png")
                    overlay_with_alpha_composite(os.path.join(TOKEN_BG_PATH, 'reminder_background.png'), leaf_array_reminder, result_image_reminder_path, mask_color=(45, 45, 45, 0))
                for reminder in character.get('remindersGlobal', []):
                    curved_reminders_path = os.path.join(CURVED_REMINDERS_PATH, f"{character['id']}_{reminder}.png")
                    plot_curved_text(reminder, radius=130, filename=curved_reminders_path, start_angle=270, margin=10, text_color = 'White')

                    leaf_array_reminder = generate_overlay_array(character, SCRAPED_IMAGES_PATH, is_reminder=True, reminder=reminder)
                    result_image_reminder_path = os.path.join(GENERATED_REMINDERS_PATH, f"{character['id']}_{reminder}.png")
                    overlay_with_alpha_composite(os.path.join(TOKEN_BG_PATH, 'reminder_background.png'), leaf_array_reminder, result_image_reminder_path, mask_color=(45, 45, 45, 0))
            except Exception as e:
                print(f"An error occurred while processing {character['id']}: {e}")