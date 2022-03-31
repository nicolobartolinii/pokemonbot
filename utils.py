import os
import random

from PIL import Image
import requests
from io import BytesIO


def compose_images(image_urls):
    bg_url, *other_urls = image_urls
    print(bg_url)
    print(other_urls)
    response_bg = requests.get(bg_url)
    image = Image.open(BytesIO(response_bg.content)).convert('RGBA')
    for fg_name in other_urls:
        response_fg = requests.get(fg_name)
        foreground = Image.open(BytesIO(response_fg.content)).convert('RGBA')
        image.paste(foreground, (foreground.width, 0), foreground)
    return image


def imagecreation(ids):  # function to create an image
    images = [f'./imagesHigh/{id.split("-")[0]}_{id.split("-")[1]}_hires.png' for id in ids]
    images = [Image.open(image).resize((367, 512)) for image in images]
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)+140
    max_height = max(heights)+60
    new_im = Image.new('RGBA', (total_width, max_height), (255, 0, 0, 0))
    x_offset = 50
    y_offset = 30
    for im in images:
        new_im.paste(im, (x_offset, y_offset))
        x_offset += im.size[0]+20
    return new_im
