# auth/stego_toolkit.py

from PIL import Image
import numpy as np
import base64
import os

DELIM = "#####"


# =====================================
# BIT HELPERS
# =====================================

def _text_to_bits(text: str) -> str:
    return "".join(format(ord(c), "08b") for c in text)


# =====================================
# CORE TEXT STEGO
# =====================================

def _hide_text_in_image(img: Image.Image, text: str) -> Image.Image:

    arr = np.array(img)
    flat = arr.flatten()

    binary = _text_to_bits(text + DELIM)

    if len(binary) > len(flat):
        raise ValueError("Payload too large for selected image")

    for i, bit in enumerate(binary):
        flat[i] = (flat[i] & 254) | int(bit)

    encoded = flat.reshape(arr.shape)
    return Image.fromarray(encoded)


def _reveal_text_from_image(img: Image.Image) -> str:

    arr = np.array(img).flatten()

    bits = []
    chars = []

    for px in arr:

        bits.append(str(px & 1))

        if len(bits) == 8:

            chars.append(chr(int("".join(bits), 2)))
            bits.clear()

            if "".join(chars).endswith(DELIM):
                return "".join(chars[:-len(DELIM)])

    raise ValueError("No hidden data detected")


# =====================================
# FILE → IMAGE
# =====================================

def hide_file_in_image(image_path: str, file_path: str, output_path: str):

    with open(file_path, "rb") as f:
        raw = f.read()

    encoded = base64.b64encode(raw).decode()

    filename = os.path.basename(file_path)

    payload = f"{filename}||{encoded}"

    img = Image.open(image_path).convert("RGB")

    stego = _hide_text_in_image(img, payload)

    if not output_path.lower().endswith((".png", ".jpg", ".jpeg")):
        output_path += ".png"

    stego.save(output_path, format="PNG")

    return output_path


# =====================================
# IMAGE → FILE
# =====================================

def reveal_file_from_image(image_path: str):

    img = Image.open(image_path).convert("RGB")

    hidden = _reveal_text_from_image(img)

    if "||" not in hidden:
        raise ValueError("No hidden data detected")

    filename, b64 = hidden.split("||", 1)

    file_bytes = base64.b64decode(b64)

    return filename, file_bytes
