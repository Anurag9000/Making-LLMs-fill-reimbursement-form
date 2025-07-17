import os
from pdf2image import convert_from_path

# Set the name of your PDF file here
pdf_file = input("Enter the name of your PDF file: ")  # Change this to your PDF file name

def pdf_to_images(pdf_file):
    # Check if the PDF file exists
    if not os.path.exists(pdf_file):
        print(f"Error: File '{pdf_file}' does not exist.")
        return

    # Convert PDF pages to images
    try:
        images = convert_from_path(pdf_file)
    except Exception as e:
        print("Error during conversion:", e)
        return

    # Create the output folder "images" if it doesn't exist
    output_folder = "images"
    os.makedirs(output_folder, exist_ok=True)

    # Save each page as an image
    for idx, image in enumerate(images, start=1):
        image_filename = os.path.join(output_folder, f"{idx}.png")
        image.save(image_filename, "PNG")
        print(f"Saved page {idx} as {image_filename}")

    print("All pages have been saved in the 'images' folder.")

if __name__ == '__main__':
    pdf_to_images(pdf_file)
