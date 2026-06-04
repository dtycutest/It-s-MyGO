"""Generate proper tab bar PNG icons using PIL with recognizable shapes."""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = r"d:\上课\大三下\计算机综合项目实践\ycg-project\frontend\src\static"
SIZE = 81
PAD = 14

def draw_home_icon(draw, color):
    """Draw a house icon."""
    x0, y0 = PAD, PAD + 6
    w = SIZE - 2 * PAD
    h = w
    
    # Roof (triangle)
    roof = [(x0 + w // 2, y0), (x0 + w, y0 + h // 3), (x0, y0 + h // 3)]
    draw.polygon(roof, outline=color, width=3)
    
    # Body (rectangle)
    body_y = y0 + h // 3
    body_h = SIZE - PAD - body_y
    draw.rectangle([(x0 + w // 8, body_y), (x0 + 7 * w // 8, body_y + body_h)], outline=color, width=3)
    
    # Door
    door_y = body_y + body_h // 3
    door_h = body_h - body_h // 3
    draw.rectangle([(x0 + w // 4, door_y), (x0 + 3 * w // 4, door_y + door_h)], outline=color, width=3)


def draw_user_icon(draw, color):
    """Draw a person icon."""
    cx = SIZE // 2
    cy = PAD + 6
    
    # Head (circle)
    r = (SIZE - 2 * PAD) // 6
    draw.ellipse([(cx - r, cy), (cx + r, cy + 2 * r)], outline=color, width=3)
    
    # Body
    body_top = cy + 2 * r + 4
    body_bottom = SIZE - PAD - 4
    body_half_w = (SIZE - 2 * PAD) // 3
    draw.ellipse([(cx - body_half_w, body_top), (cx + body_half_w, body_bottom)], outline=color, width=3)


icons = [
    ("home-active.png", "#FF6B35", draw_home_icon),
    ("home-inactive.png", "#999999", draw_home_icon),
    ("user-active.png", "#FF6B35", draw_user_icon),
    ("user-inactive.png", "#999999", draw_user_icon),
]

for filename, color_hex, draw_fn in icons:
    img = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw_fn(draw, color_hex)
    path = os.path.join(BASE, filename)
    img.save(path)
    print(f"Created {filename} ({os.path.getsize(path)} bytes)")

print("Done")