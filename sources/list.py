import json
import argparse

# Lists the titles of templates with missing images
# python3 list.py target_template.json list_titles_with_missing_images.txt

def find_titles_with_missing_image(input_file, output_file):
    # Load the JSON data
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Find all titles with the specified error
    titles_with_missing_image = set()
    for item in data.get('templates', []):
        if "Missing 'image' property" in item.get('__comment__', ''):
            titles_with_missing_image.add(item.get('title'))

    # Sort the titles alphabetically
    sorted_titles = sorted(titles_with_missing_image)

    # Save the titles to a text file with '|' as the delimiter
    with open(output_file, 'w') as file:
        for title in sorted_titles:
            file.write(f"{title}|\n")

    print(f"Found {len(titles_with_missing_image)} unique titles with the 'Missing \'image\' property' error.")

def main():
    parser = argparse.ArgumentParser(description="Find titles with missing image property in JSON templates.")
    parser.add_argument('input_file', type=str, help='The input JSON file.')
    parser.add_argument('output_file', type=str, help='The output text file.')

    args = parser.parse_args()

    find_titles_with_missing_image(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
