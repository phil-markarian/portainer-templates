import os
import string
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(filename='combine_and_remove.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Set up template update logging
template_update_logger = logging.getLogger('template_updates')
template_update_logger.setLevel(logging.INFO)
template_update_handler = logging.FileHandler('template_updates.log')
template_update_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
template_update_logger.addHandler(template_update_handler)

# Check if template_updates.log exists and initialize it if not
template_updates_log_exists = os.path.exists('template_updates.log')
if not template_updates_log_exists:
    with open('template_updates.log', 'w') as log_file:
        log_file.write("Template updates log initialized.\n")
    template_update_logger.info("Template updates log initialized.")

# Source: https://ask.replit.com/t/how-do-i-make-colored-text-in-python/29288/18
reset_color = "\033[0m"  # Important!

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

# Get list of files in sources
dir = os.path.dirname(os.path.abspath(__file__))
templates_src_dir = os.path.join(dir, '../sources/')
template_dest_file = os.path.join(dir, '../templates.json')
files = os.listdir(templates_src_dir)

# Initialize empty list to store template objects
templates = []

# Load existing templates from templates.json if it exists
existing_templates = {}
if os.path.exists(template_dest_file):
    with open(template_dest_file, 'r') as f:
        existing_data = json.load(f)
        existing_templates = {template['title']: template for template in existing_data['templates']}

# For each file in sources
for file in files:
    file_path = os.path.join(templates_src_dir, file)
    if os.path.isfile(file_path) and file.endswith('.json'):
        with open(file_path) as f:
            try:
                # Load the JSON into a variable
                data = json.load(f)['templates']
                # Append the template object to the templates list
                templates.extend(data)
                logging.info(f"Successfully loaded templates from {file}")
            except json.decoder.JSONDecodeError as err:
                logging.error(f"Skipping {file} due to a JSON decoding error: {err.msg}")
                print(f'{rgb(255, 0, 0)}Skipping one of the sources due to an error:{reset_color} {f.name}')
                print(f'Error msg: {err.msg}')
            except KeyError as err:
                logging.error(f"Skipping {file} due to a missing key error: {err}")
                print(f'{rgb(255, 0, 0)}Skipping one of the sources due to a missing key error:{reset_color} {f.name}')
                print(f'Error msg: {err}')

seen_titles = set()
filtered_data = []

def normalize_string(original, lowercase=True):
    normalized = original.translate(str.maketrans('', '', string.punctuation)).replace(' ', '')
    return normalized.lower() if lowercase else normalized.capitalize()

for template in templates:
    normalized_title = normalize_string(template['title'])
    if normalized_title not in seen_titles:
        seen_titles.add(normalized_title)
        # Normalize categories
        categories = template.get('categories', [])
        normalized_categories = []
        for category in categories:
            normalized_category = normalize_string(category, lowercase=False)
            if normalized_category not in normalized_categories:
                normalized_categories.append(normalized_category)
        template['categories'] = normalized_categories
        filtered_data.append(template)
        
        # Check if the template is new or modified
        if not template_updates_log_exists or template['title'] not in existing_templates or template != existing_templates[template['title']]:
            template_update_logger.info(f"Added or modified template: {template['title']}")
    else:
        logging.info(f"Removed duplicate template: {template['title']}")

file_data = {
    'version': '2',
    'templates': filtered_data
}

# Open the templates.json file, and write results to it
with open(template_dest_file, 'w') as f:
    json.dump(file_data, f, indent=2, sort_keys=False)
    logging.info(f"Combined templates written to {template_dest_file}")
    print(f'{rgb(0, 255, 0)}Combined templates written to {template_dest_file}{reset_color}')
