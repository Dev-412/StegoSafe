import requests
from io import BytesIO
from PIL import Image
import numpy as np

DELIM = "#####"

def hide_text_in_image(img, text):

    arr = np.array(img)

    binary = ''.join(format(ord(c), '08b') for c in text)
    binary += ''.join(format(ord(c), '08b') for c in DELIM)

    flat = arr.flatten()

    if len(binary) > len(flat):
        raise Exception("Too much data for this image")

    for i in range(len(binary)):
        flat[i] = (flat[i] & 254) | int(binary[i])


    encoded = flat.reshape(arr.shape)

    return Image.fromarray(encoded)



def reveal_text_from_url(url):

    r = requests.get(url, timeout=10)
    img = Image.open(BytesIO(r.content)).convert("RGB")

    arr = np.array(img).flatten()

    bits = []
    chars = []

    for px in arr:
        bits.append(str(px & 1))

        if len(bits) == 8:
            c = chr(int("".join(bits), 2))
            chars.append(c)
            bits = []

            if "".join(chars).endswith(DELIM):
                return "".join(chars[:-5])

    return ""