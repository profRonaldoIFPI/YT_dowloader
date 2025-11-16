import os
from PIL import Image, ImageDraw

def create_icon(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # background circle
    d.ellipse([(16, 16), (size-16, size-16)], fill=(25, 25, 25, 255))

    # play triangle
    tri = [(size*0.42, size*0.35), (size*0.42, size*0.65), (size*0.68, size*0.5)]
    d.polygon(tri, fill=(255, 255, 255, 255))

    # download arrow
    d.rectangle([(size*0.24, size*0.28), (size*0.34, size*0.52)], fill=(76, 175, 80, 255))
    d.polygon([(size*0.19, size*0.52), (size*0.29, size*0.72), (size*0.39, size*0.52)], fill=(76, 175, 80, 255))

    # save as ico with multiple sizes
    img.save(path, sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])

if __name__ == "__main__":
    create_icon(os.path.join("assets", "video_download.ico"))