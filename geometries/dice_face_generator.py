from PIL import Image, ImageDraw
import random

# Define the size of each dice face image
size = 200

# Create a dictionary to store the file paths of the dice face images
dice_faces = {}

# Loop over each possible dice face value (1-6)
for i in range(1, 7):
    # Create a new image and a drawing context
    image = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(image)
    
    # Draw the dots on the dice face based on the value
    if i == 1:
        draw.ellipse((size//2-20, size//2-20, size//2+20, size//2+20), fill='black')
    elif i == 2:
        draw.ellipse((size//4-20, size//4-20, size//4+20, size//4+20), fill='black')
        draw.ellipse((3*size//4-20, 3*size//4-20, 3*size//4+20, 3*size//4+20), fill='black')
    elif i == 3:
        draw.ellipse((size//4-20, size//4-20, size//4+20, size//4+20), fill='black')
        draw.ellipse((size//2-20, size//2-20, size//2+20, size//2+20), fill='black')
        draw.ellipse((3*size//4-20, 3*size//4-20, 3*size//4+20, 3*size//4+20), fill='black')
    elif i == 4:
        draw.ellipse((size//4-20, size//4-20, size//4+20, size//4+20), fill='black')
        draw.ellipse((size//4-20, 3*size//4-20, size//4+20, 3*size//4+20), fill='black')
        draw.ellipse((3*size//4-20, size//4-20, 3*size//4+20, size//4+20), fill='black')
        draw.ellipse((3*size//4-20, 3*size//4-20, 3*size//4+20, 3*size//4+20), fill='black')
    elif i == 5:
        draw.ellipse((size//4-20, size//4-20, size//4+20, size//4+20), fill='black')
        draw.ellipse((size//4-20, 3*size//4-20, size//4+20, 3*size//4+20), fill='black')
        draw.ellipse((size//2-20, size//2-20, size//2+20, size//2+20), fill='black')
        draw.ellipse((3*size//4-20, size//4-20, 3*size//4+20, size//4+20), fill='black')
        draw.ellipse((3*size//4-20, 3*size//4-20, 3*size//4+20, 3*size//4+20), fill='black')
    elif i == 6:
        draw.ellipse((size//4-20, size//4-20, size//4+20, size//4+20), fill='black')
        draw.ellipse((size//4-20, size//2-20, size//4+20, size//2+20), fill='black')
        draw.ellipse((size//4-20, 3*size//4-20, size//4+20, 3*size//4+20), fill='black')
        draw.ellipse((3*size//4-20, size//4-20, 3*size//4+20, size//4+20), fill='black')
        draw.ellipse((3*size//4-20, size//2-20, 3*size//4+20, size//2+20), fill='black')
        draw.ellipse((3*size//4-20, 3*size//4-20, 3*size//4+20, 3*size//4+20), fill='black')

    # Save the image to a file and store the file path in the dictionary
    image_path = f'dice_face_{i}.png'
    image.save(image_path)
    dice_faces[i] = image_path
