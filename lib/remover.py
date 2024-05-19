import json
import os
import re

# Directory containing the JSON files
directory = '../portainer-templates/sources/'

# Function to check if a template has errors and return the errors
def get_errors(template):
    errors = []
    if template.get('type', 0) not in [1, 2, 3]:
        errors.append(f"Invalid type: {template.get('type')}")
    if 'image' not in template:
        errors.append("Missing 'image' property")
    if 'volumes' in template:
        for volume in template['volumes']:
            if 'container' not in volume:
                errors.append(f"Invalid volume: {volume}")
    if 'ports' in template:
        port_pattern = re.compile(r'^([0-9]*+(-[0-9]+)?(:[0-9]*+(-[0-9]+)?)?)(/(tcp|udp))?$')
        for port in template['ports']:
            if not port_pattern.match(port):
                errors.append(f"Invalid port: {port}")
    return errors

def save_json_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

all_faulty_templates = []

# Process each JSON file in the directory
for root, _, files in os.walk(directory):
    for filename in files:
        if filename.endswith('.json') and filename != 'all_errors.json':  # Skip the all_errors.json file
            filepath = os.path.join(root, filename)
            
            # Load the JSON file
            with open(filepath, 'r') as file:
                data = json.load(file)
            
            # Separate valid and faulty templates
            valid_templates = []
            faulty_templates = []
            
            for index, template in enumerate(data.get('templates', [])):
                errors = get_errors(template)
                if errors:
                    faulty_template_with_comments = {"__comment__": " | ".join(errors)}
                    faulty_template_with_comments.update(template)
                    faulty_templates.append((index, faulty_template_with_comments))
                    all_faulty_templates.append(faulty_template_with_comments)
                else:
                    valid_templates.append(template)
            
            # Save the valid templates back to the original file
            data['templates'] = valid_templates
            with open(filepath, 'w') as file:
                json.dump(data, file, indent=4)
            
            # Save each faulty template to a separate file in a new folder
            if faulty_templates:
                error_folder = os.path.join(root, filename.replace('.json', '_errors'))
                os.makedirs(error_folder, exist_ok=True)
                
                for index, faulty_template in faulty_templates:
                    error_filepath = os.path.join(error_folder, f'templates_{index}.json')
                    save_json_file(error_filepath, faulty_template)
                    print(f'Saved invalid template {index} to {error_filepath}')
                
                print(f"Processed {filename}: {len(faulty_templates)} faulty templates moved to '{error_folder}'")
            else:
                print(f"Processed {filename}: No faulty templates found")

# Save all faulty templates to a comprehensive file
all_errors_filepath = os.path.join(directory, 'all_errors.json')
save_json_file(all_errors_filepath, {"templates": all_faulty_templates})
print(f"Saved all faulty templates to {all_errors_filepath}")

print("Processing complete.")
