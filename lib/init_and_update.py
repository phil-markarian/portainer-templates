import os
import csv
import requests
import json
import logging
from jsonschema import validate, ValidationError
from time import sleep
from datetime import datetime

# Define paths
dir = os.path.dirname(os.path.abspath(__file__))
destination_dir = os.path.join(dir, '../sources')
sources_list = os.path.join(dir, '../sources.csv')
schema_path = os.path.join(dir, '../Schema.json')
processed_templates_file = os.path.join(dir, '../processed_templates.json')

# Set up logging
logging.basicConfig(filename=os.path.join(destination_dir, 'template_processing.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load processed templates from file
if os.path.exists(processed_templates_file):
    with open(processed_templates_file, 'r') as file:
        processed_templates = json.load(file)
else:
    processed_templates = {}

# Load the JSON schema
with open(schema_path, 'r') as schema_file:
    schema = json.load(schema_file)

# Placeholder values for missing required properties
placeholder_values = {
    "categories": ["default"],
    "image": "placeholder_image",
    "type": 1,  # Default to container type
    "description": "Placeholder description",
    "title": "Placeholder title"
}

# Rate limit handling
def check_rate_limit(response):
    if 'X-RateLimit-Remaining' in response.headers:
        remaining = int(response.headers['X-RateLimit-Remaining'])
        limit = int(response.headers.get('X-RateLimit-Limit', 0))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        if remaining == 0:
            wait_time = max(reset_time - int(datetime.now().timestamp()), 0)
            logging.warning(f"Rate limit reached. Limit is {limit} requests per minute. Waiting {wait_time} seconds until {datetime.fromtimestamp(reset_time)} before retrying.")
            sleep(wait_time)
            return True
    if response.status_code == 429:
        retry_after = int(response.headers.get('X-Retry-After', 60))
        logging.warning(f"Rate limit reached. Waiting {retry_after} seconds before retrying.")
        sleep(retry_after)
        return True
    return False

# Check rate limit before proceeding
def check_initial_rate_limit():
    url = "https://hub.docker.com/v2/repositories/library/hello-world"
    try:
        response = requests.get(url)
        response.raise_for_status()
        check_rate_limit(response)
    except requests.RequestException as e:
        logging.error(f"Error checking rate limit: {e}")
        raise

# Downloads the file from a given URL, to the local destination
def download(url: str, filename: str, max_retries: int = 3):
    file_path = os.path.join(destination_dir, filename)
    attempt = 0
    while attempt < max_retries:
        try:
            r = requests.get(url, stream=True, timeout=10)
            if check_rate_limit(r):
                attempt += 1
                continue
            if r.ok:
                logging.info(f'Saving to {os.path.abspath(file_path)}')
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 8):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                            os.fsync(f.fileno())
                return file_path
            else:  # HTTP status code 4XX/5XX
                logging.error(f'Download failed: status code {r.status_code}\n{r.text}')
                attempt += 1
                sleep(2)  # Wait for 2 seconds before retrying
        except (requests.exceptions.RequestException, OSError) as e:
            logging.error(f'Error during download attempt {attempt + 1}: {e}')
            attempt += 1
            sleep(2)  # Wait for 2 seconds before retrying
    logging.warning(f'Failed to download {url} after {max_retries} attempts.')
    return None

# Fetch Docker image from Docker Hub
def fetch_docker_image(title):
    search_url = f"https://hub.docker.com/v2/search/repositories/?query={title}"
    try:
        response = requests.get(search_url)
        if check_rate_limit(response):
            return placeholder_values['image']
        response.raise_for_status()
        results = response.json().get('results', [])
        if results:
            return results[0]['repo_name']  # Return the repo_name of the first search result
    except requests.RequestException as e:
        logging.error(f"Error fetching Docker image for {title}: {e}")
    return placeholder_values['image']  # Return placeholder if no result found or an error occurred

# Fetch description and categories from Docker Hub
def fetch_docker_info(image):
    if '/' in image:
        namespace, repo_name = image.split('/', 1)
        repo_name = repo_name.split(':', 1)[0]  # Remove tag from repo_name
        url = f"https://hub.docker.com/v2/repositories/{namespace}/{repo_name}/"
    else:
        url = f"https://hub.docker.com/v2/repositories/{image}/"

    try:
        response = requests.get(url)
        if check_rate_limit(response):
            return placeholder_values['description'], placeholder_values['categories']
        response.raise_for_status()
        repository_info = response.json()
        description = repository_info.get('description', placeholder_values['description'])
        categories = [category['name'] for category in repository_info.get('categories', [])]
        if not categories:
            categories = placeholder_values['categories']
        return description, categories
    except requests.RequestException as e:
        logging.error(f"Error fetching info for {image}: {e}")
    return placeholder_values['description'], placeholder_values['categories']  # Return placeholders if an error occurred

# Gets list of URLs to download from CSV file
def get_source_list():
    sources = []
    try:
        with open(sources_list, mode='r') as file:
            csvFile = csv.reader(file)
            for lines in csvFile:
                if len(lines) > 1 and lines[1].strip():
                    sources.append(lines)
    except FileNotFoundError as e:
        logging.error(f"Error reading sources file: {e}")
    return sources

# Validate and fix JSON file against the schema
def validate_and_fix_json(file_path: str):
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON file: {file_path}. Error: {e}")
            return False

        edited = False
        edit_info = {}

        # Check for required properties and add placeholders if missing
        if 'templates' in data:
            for template in data['templates']:
                if 'image' not in template:
                    fetched_image = fetch_docker_image(template['title'])
                    template['image'] = fetched_image
                    if fetched_image != placeholder_values['image']:
                        if template['title'] not in edit_info:
                            edit_info[template['title']] = []
                        edit_info[template['title']].append("{image} fetched from Docker Hub")
                        edited = True

                if 'description' not in template or 'categories' not in template:
                    if 'image' in template:
                        try:
                            fetched_description, fetched_categories = fetch_docker_info(template['image'])
                            if 'description' not in template:
                                template['description'] = fetched_description
                                if fetched_description != placeholder_values['description']:
                                    if template['title'] not in edit_info:
                                        edit_info[template['title']] = []
                                    edit_info[template['title']].append("{description} fetched from Docker Hub")
                                    edited = True
                            if 'categories' not in template:
                                template['categories'] = fetched_categories
                                if fetched_categories != placeholder_values['categories']:
                                    if template['title'] not in edit_info:
                                        edit_info[template['title']] = []
                                    edit_info[template['title']].append("{categories} fetched from Docker Hub")
                                    edited = True
                        except Exception as e:
                            logging.error(f"Error fetching description and categories for template '{template['title']}': {str(e)}")
                    else:
                        if 'description' not in template:
                            template['description'] = placeholder_values['description']
                            if template['title'] not in edit_info:
                                edit_info[template['title']] = []
                            edit_info[template['title']].append("{description} placeholder used")
                            edited = True
                        if 'categories' not in template:
                            template['categories'] = placeholder_values['categories']
                            if template['title'] not in edit_info:
                                edit_info[template['title']] = []
                            edit_info[template['title']].append("{categories} placeholder used")
                            edited = True

                for key, placeholder in placeholder_values.items():
                    if key not in template:
                        template[key] = placeholder
                        if template['title'] not in edit_info:
                            edit_info[template['title']] = []
                        edit_info[template['title']].append(f"{{{key}}}")
                        edited = True

                # Fix invalid properties
                if 'type' in template and template['type'] not in [1, 2, 3]:
                    template['type'] = placeholder_values['type']
                    edited = True
                    if template['title'] not in edit_info:
                        edit_info[template['title']] = []
                    edit_info[template['title']].append("{type} changed to 1")
                if 'description' in template and not isinstance(template['description'], str):
                    template['description'] = placeholder_values['description']
                    edited = True
                    if template['title'] not in edit_info:
                        edit_info[template['title']] = []
                    edit_info[template['title']].append("{description}")

        if edited:
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2)
        
        try:
            validate(instance=data, schema=schema)
            logging.info(f"Validation successful for {file_path}")
            if edited:
                for title, fields in edit_info.items():
                    logging.info(f"Updated fields for {title}: {', '.join(fields)}")  # Log the updated fields
            return True
        except ValidationError as e:
            logging.error(f"Validation error in {file_path}: {e.message}")
            return False

# Main function to check for new templates and run download and validation
def main():
    check_initial_rate_limit()
    source_list = get_source_list()
    
    for source in source_list:
        source_name, source_url = source
        existing_templates = processed_templates.get(source_url, [])
        
        try:
            response = requests.get(source_url)
            response.raise_for_status()
            source_data = response.json()
            
            new_templates = []
            for template in source_data.get('templates', []):
                if template['title'] not in existing_templates:
                    new_templates.append(template)
            
            if new_templates:
                logging.info(f"New templates found in {source_name}: {[template['title'] for template in new_templates]}")
                filename = f"{source_name}.json"
                downloaded_file = download(source_url, filename)
                if downloaded_file:
                    if not validate_and_fix_json(downloaded_file):
                        os.remove(downloaded_file)
                        logging.warning(f"Deleted invalid file {downloaded_file}")
                    else:
                        processed_templates[source_url] = [template['title'] for template in source_data.get('templates', [])]
            else:
                logging.info(f"No new templates found in {source_name}.")
        except requests.RequestException as e:
            logging.error(f"Error fetching source file {source_name}: {e}")
    
    # Save processed templates to file
    with open(processed_templates_file, 'w') as file:
        json.dump(processed_templates, file, indent=2)

if __name__ == "__main__":
    main()