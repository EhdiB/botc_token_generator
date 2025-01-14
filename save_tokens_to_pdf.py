import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from PIL import Image

IMG_TOKEN_PATH = 'img/token'
output_tokens_pdf_path = 'tokens_printable.pdf'
output_reminders_pdf_path = 'reminders_printable.pdf'

generated_tokens_folder_path = os.path.join(IMG_TOKEN_PATH, 'generated_tokens')
generated_reminders_folder_path = os.path.join(IMG_TOKEN_PATH, 'generated_reminders')

def images_to_pdf(folder_path, output_pdf_path, duplicates_tokens=False, image_new_size=1.0, side_margin=1.0, between_margin=0.5, background_color=None):
    """
    Convert images in a folder to a single PDF, fitting as many images on a page as possible.
    
    Args:
    - folder_path (str): Path to the folder containing images.
    - output_pdf_path (str): Path for the output PDF file.
    - scale_factor (float): Factor to scale the images by. Default is 1.0 (no scaling).
    - side_margin (float): Margin on the sides of the page in inches. Default is 1.0 inch.
    - between_margin (float): Margin between images in inches. Default is 0.5 inch.
    - background_color (tuple): Background color in RGB format. Default is None (white).
    """
    try:
        # Constants for A4 page size and conversions
        page_width, page_height = A4
        side_margin = side_margin * inch  # Convert margin to points
        between_margin = between_margin * inch  # Convert margin to points
        
        # Initialize PDF
        c = canvas.Canvas(output_pdf_path, pagesize=A4)
        
        def set_background():
            if background_color:
                c.setFillColorRGB(background_color[0]/255.0, background_color[1]/255.0, background_color[2]/255.0)
                c.rect(0, 0, page_width, page_height, stroke=0, fill=1)
        
        set_background()  # Set background color for the first page
        
        # Process images
        images_dict = {f: 1 for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))}
        # Only update values if the keys already exist in the dictionary
        if duplicates_tokens:
            for key, value in [('legion.png', 8), ('riot.png', 4), ('villageidiot.png', 3), ('imp.png', 2)]:
                if key in images_dict:
                    images_dict[key] = value
        images_dict = {key: images_dict[key] for key in sorted(images_dict)}
        
        x_offset, y_offset = side_margin, page_height - side_margin  # Initialize offsets
        
        for image, count in images_dict.items():
            for i in range(count):
                img_path = os.path.join(folder_path, image)
                print("placing: "+ image)
                with Image.open(img_path) as img:
                    # Scale image if needed
                    # print(int(img.width),int(img.height),int(img.height),scale_factor, int(img.height*scale_factor))
                    img = img.resize((image_new_size, image_new_size))


                    # Calculate position for the next image
                    if x_offset + img.width > page_width - side_margin:
                        x_offset = side_margin
                        y_offset -= img.height + between_margin

                    if y_offset - img.height < side_margin:
                        c.showPage()  # Start a new page
                        y_offset = page_height - side_margin
                        set_background()  # Set background color for the new page

                    # Draw image
                    c.drawInlineImage(img_path, x_offset, y_offset - img.height, width=img.width, height=img.height)
                    x_offset += img.width + between_margin
                
        c.save()
        print(f"PDF generated successfully: {output_pdf_path}")
    except Exception as e:
        print(f"An error occurred while generating the PDF: {e}")

if __name__ == "__main__":
    # Example usage for tokens and reminders with background color set to light gray
    images_to_pdf(generated_tokens_folder_path, output_tokens_pdf_path, duplicates_tokens=True, image_new_size = 85, side_margin=0.5, between_margin=0.10, background_color=(86, 68, 46))
    # 614 614 614 0.13 79
    images_to_pdf(generated_reminders_folder_path, output_reminders_pdf_path, image_new_size=55, side_margin=0.5, between_margin=0.10, background_color=(45, 45, 45))
    # 255 255 255 0.2 51