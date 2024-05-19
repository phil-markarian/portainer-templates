import json
import argparse

# In your output for list, add image after | and then run this file to fix your files
# python3 fix.py input_json_file.json images_file.txt output_json_file.json

def update_json_with_images(json_file, text_file, output_file):
    # Load the list of titles and images from the text file
    title_to_image = {}
    with open(text_file, 'r') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 2:
                title, image = parts
                title_to_image[title.strip()] = image.strip()

    # Load the JSON data
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Update the JSON data with the image property and remove the __comment__ property
    for item in data.get('templates', []):
        title = item.get('title')
        if title in title_to_image:
            item['image'] = title_to_image[title]
        item.pop('__comment__', None)

    # Save the updated JSON data
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Updated {len(data.get('templates', []))} templates.")

def main():
    parser = argparse.ArgumentParser(description="Update JSON templates with images from a text file.")
    parser.add_argument('json_file', type=str, help='The input JSON file.')
    parser.add_argument('text_file', type=str, help='The text file containing titles and images.')
    parser.add_argument('output_file', type=str, help='The output JSON file.')

    args = parser.parse_args()

    update_json_with_images(args.json_file, args.text_file, args.output_file)

if __name__ == "__main__":
    main()
