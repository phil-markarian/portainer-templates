import os
import string
import json

# Source: https://ask.replit.com/t/how-do-i-make-colored-text-in-python/29288/18
reset_color = "\033[0m"  # Important!
def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

# Define paths
dir = os.path.dirname(os.path.abspath(__file__))
template_dest_file = os.path.join(dir, '../templates.json')

# Function to sort dictionary keys recursively
def sort_dict(d):
    if isinstance(d, dict):
        return {k: sort_dict(v) for k, v in sorted(d.items())}
    if isinstance(d, list):
        return [sort_dict(i) for i in d]
    return d

# Read the templates.json file
with open(template_dest_file, 'r') as file:
    data = json.load(file)

# Sort the templates list by 'title'
data['templates'] = sorted(data['templates'], key=lambda x: x.get('title', '').lower())

# Sort the keys of each template in the 'templates' list
data['templates'] = [sort_dict(template) for template in data['templates']]

# Write the sorted JSON back to the templates.json file
with open(template_dest_file, 'w') as file:
    json.dump(data, file, indent=2)

print(f'{rgb(0, 255, 0)}Alphabetized templates written to {template_dest_file}{reset_color}')
