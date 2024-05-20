import json
import argparse

# Alphabetizes your templates for easier tracking of diffs.
# python3 alphabetize target_template.json aphabetized.json
def sort_dict(d):
    """Recursively sort dictionary keys."""
    if isinstance(d, dict):
        return {k: sort_dict(v) for k, v in sorted(d.items())}
    if isinstance(d, list):
        return [sort_dict(i) for i in d]
    return d

def alphabetize_json(input_file, output_file):
    # Read the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)
    
    # Sort the templates list by 'title'
    data['templates'] = sorted(data['templates'], key=lambda x: x.get('title', ''))

    # Sort the keys of each template in the 'templates' list
    data['templates'] = [sort_dict(template) for template in data['templates']]

    # Write the sorted JSON back to a file
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)
    
    print(f"Alphabetized JSON has been written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Alphabetize JSON templates by title and keys.')
    parser.add_argument('input_file', type=str, help='The input JSON file.')
    parser.add_argument('output_file', type=str, help='The output JSON file.')

    args = parser.parse_args()

    alphabetize_json(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
