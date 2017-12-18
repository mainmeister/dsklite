import pystray

width = 16
height = 16
color1 = "#ff0000"
color2 = "#000000"

icon = pystray.Icon('test name')
from PIL import Image, ImageDraw

# Generate an image
image = Image.new('RGB', (width, height), color1)
dc = ImageDraw.Draw(image)
dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
dc.rectangle((0, height // 2, width // 2, height), fill=color2)

icon.icon = image

def setup(icon):
    print "running"
    icon.visible = True

icon.run(setup)
