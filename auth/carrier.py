import random
from PIL import Image
import os

BASE_DIR = os.path.dirname(__file__)
CARRIER_DIR = os.path.join(BASE_DIR, "carriers")

def get_random_image(w=400, h=400):

    files = [
        f for f in os.listdir(CARRIER_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not files:
        raise Exception("No carrier images found")

    pick = random.choice(files)

    path = os.path.join(CARRIER_DIR, pick)

    img = Image.open(path).convert("RGB")

    img = img.resize((w, h))

    return img
