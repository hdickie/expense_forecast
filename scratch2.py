
import os
from PIL import Image
import pillow_avif

def replace_transparency_with_white(img):
    if img.mode == 'RGBA':
        # Create a white background image
        background = Image.new('RGB', img.size, (255, 255, 255))
        # Paste the image on the white background using alpha as a mask
        background.paste(img, mask=img.split()[3])  # Use the alpha channel as mask
        return background
    else:
        return img.convert('RGB')

def convert_avif_to_png(filename):
    img = Image.open(filename)
    img_with_white_bg = replace_transparency_with_white(img)
    img_with_white_bg.save(filename.replace('avif','png'))

def convert_webp_to_png(filename):
    webp_image = Image.open(filename)
    webp_image = replace_transparency_with_white(webp_image)
    png_image = webp_image.convert("RGBA")
    png_image.save(filename.replace('webp','png'))

if __name__ == '__main__':
    pass
    os.chdir('/Users/hume/Desktop/tmp')
    for f in os.listdir('.'):
        if 'avif' in f:
            convert_avif_to_png(f)
        if 'webp' in f:
            convert_webp_to_png(f)