from PIL import Image
import numpy as np

DELIM = "#####"

def hide_text(img_path, text, out_path):

    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)

    binary = ''.join(format(ord(c), '08b') for c in text)
    binary += ''.join(format(ord(c), '08b') for c in DELIM)

    flat = arr.flatten()

    if len(binary) > len(flat):
        raise Exception("Message too large for this image")

    for i in range(len(binary)):
        flat[i] = (flat[i] & ~1) | int(binary[i])

    encoded = flat.reshape(arr.shape)

    Image.fromarray(encoded).save(out_path)

    return out_path


def reveal_text(img_path):

    img = Image.open(img_path)
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
