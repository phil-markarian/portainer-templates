import json
import argparse

# Removes any duplicates of templates
# python3 target_templates.json no_duplicate_templates.json

def remove_duplicates(input_file, output_file):
    # Load the JSON data
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Dictionary to keep track of unique templates
    unique_templates = {}
    
    # Process templates
    for template in data.get('templates', []):
        title = template.get('title')
        if title not in unique_templates:
            unique_templates[title] = template
        else:
            print(f"Duplicate found: {title}")

    # Update the data with unique templates
    data['templates'] = list(unique_templates.values())

    # Save the updated JSON data
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)
    
    print(f"Removed duplicates. {len(unique_templates)} unique templates have been written to {output_file}")

    # Print out all unique titles
    print("Unique titles:")
    for title in unique_templates.keys():
        print(title)

def main():
    parser = argparse.ArgumentParser(description="Remove duplicate templates from JSON.")
    parser.add_argument('input_file', type=str, help='The input JSON file.')
    parser.add_argument('output_file', type=str, help='The output JSON file.')

    args = parser.parse_args()

    remove_duplicates(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
