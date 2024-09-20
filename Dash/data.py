import shutil
from PIL import Image
import os

# Copy nfl.db from ../Scrapers to data/
shutil.copy("../Scrapers/nfl.db", "data/")
shutil.copy("../Scrapers/data/all_passing_rushing_receiving.csv", "data/")

# Define the folder containing your images
image_folder = "assets/"

# Desired size (width, height)
target_size = (150, 100)

# Function to resize an image while maintaining its aspect ratio
def resize_image(input_path, target_size):
    with Image.open(input_path) as img:
        img.thumbnail(target_size, Image.Resampling.LANCZOS)  # Resize with aspect ratio
        img.save(input_path)  # Overwrite the original image

# Loop through all the files in the assets folder
for filename in os.listdir(image_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        input_path = os.path.join(image_folder, filename)

        resize_image(input_path, target_size)
        print(f"Resized {filename} and saved to {input_path}")

print("Resizing completed!")


# Define the folder containing your images

# image_folder = "assets/"

# # Desired height
# target_height = 100

# # Function to resize an image while maintaining its aspect ratio
# def resize_image(input_path, target_height):
#     with Image.open(input_path) as img:
#         # Calculate the target width to maintain the aspect ratio
#         aspect_ratio = img.width / img.height
#         target_width = int(target_height * aspect_ratio)
        
#         # Resize image using the calculated width and target height
#         img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)  # Update to LANCZOS
#         img.save(input_path)  # Overwrite the original image

# # Loop through all the files in the assets folder
# for filename in os.listdir(image_folder):
#     if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
#         input_path = os.path.join(image_folder, filename)

#         resize_image(input_path, target_height)
#         print(f"Resized {filename} and saved to {input_path}")

# print("Resizing completed!")
