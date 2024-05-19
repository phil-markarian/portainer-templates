import json
import os
import sys
import re
import argparse
from jsonschema import validate, ValidationError, Draft7Validator

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def print_validation_errors(errors):
    for error in errors:
        print('Validation error:', error.message)
        json_obj = error.instance
        if isinstance(json_obj, dict):
            identifier = json_obj.get('title', 'Unknown')
            print('Title of invalid template:', identifier)
        print('Error at path:', list(error.path))
        print('Error at schema path:', list(error.schema_path))
        print('---')

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

def main():
    parser = argparse.ArgumentParser(description='Validate templates.json against Schema.json')
    parser.add_argument('--templates', type=str, default=os.path.join('..', 'templates.json'),
                        help='Path to the templates.json file')
    args = parser.parse_args()

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))

        schema_file = os.path.join(script_dir, '..', 'Schema.json')
        templates_file = os.path.join(script_dir, args.templates)

        schema = load_json_file(schema_file)
        templates = load_json_file(templates_file)

        validator = Draft7Validator(schema)
        errors = sorted(validator.iter_errors(templates), key=lambda e: e.path)

        faulty_templates = []
        for template in templates.get('templates', []):
            validation_errors = get_errors(template)
            if validation_errors:
                faulty_template_with_comments = {"__comment__": " | ".join(validation_errors)}
                faulty_template_with_comments.update(template)
                faulty_templates.append(faulty_template_with_comments)

        if not errors and not faulty_templates:
            print('✅ templates.json is valid against the schema and additional checks')
        else:
            if errors:
                print_validation_errors(errors)
            if faulty_templates:
                print("Templates with additional validation errors:")
                for faulty_template in faulty_templates:
                    print(json.dumps(faulty_template, indent=2))
            sys.exit(1)

    except FileNotFoundError as fnfe:
        print(f'File not found error: {fnfe}')
        sys.exit(1)
    except json.JSONDecodeError as jde:
        print(f'JSON decoding error: {jde}')
        sys.exit(1)
    except ValidationError as ve:
        print(f'Schema validation error: {ve}')
        sys.exit(1)
    except Exception as e:
        print(f'Unexpected error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
