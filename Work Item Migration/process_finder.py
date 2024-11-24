import requests
from requests.auth import HTTPBasicAuth
import argparse
import re  # For sanitizing the reference name

def get_projects(instance, collection, auth):
    url = f'{instance}/{collection}/_apis/projects?api-version=6.0'
    response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'})
    return response.json().get('value', []) if response.status_code == 200 else []

def get_processes(instance, collection, auth):
    url = f'{instance}/{collection}/_apis/work/processes?api-version=6.0-preview.2'
    response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'})
    return response.json().get('value', []) if response.status_code == 200 else []

def get_project_properties(instance, collection, project_id, auth):
    url = f'{instance}/{collection}/_apis/projects/{project_id}/properties?api-version=6.0-preview.1'
    response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'})
    return response.json().get('value', []) if response.status_code == 200 else []

def find_process(processes, process_template_id):
    for process in processes:
        if process['typeId'] == process_template_id:
            return process
    return None

def sanitize_reference_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', name)  
    sanitized = sanitized.replace(' ', '_')  
    if sanitized.lower().startswith('system'):
        sanitized = f"custom_{sanitized}"  
    return sanitized

def create_inherited_process(instance, collection, auth, parent_process_name, parent_process_id):
    url = f'{instance}/{collection}/_apis/work/processes?api-version=6.0-preview.2'
    process_name = f"{parent_process_name}-custom-template"
    reference_name = sanitize_reference_name(process_name)
    payload = {
        "name": process_name,
        "parentProcessTypeId": parent_process_id,
        "referenceName": reference_name,
        "description": f"Custom process inherited from {parent_process_name}"
    }
    response = requests.post(url, json=payload, auth=auth, headers={'Content-Type': 'application/json'})
    if response.status_code == 201:  
        created_process = response.json()
        return created_process['typeId'], created_process['name']
    elif response.status_code == 200:  # Already existing process
        created_process = response.json()
        return created_process['typeId'], created_process['name']
    elif response.status_code == 500:  # Handle specific error for existing process
        error_data = response.json()
        if error_data.get("typeKey") == "ProcessNameConflictException":
            print(f"Process '{process_name}' already exists.")
            return "Inherited/Custom", process_name
    
    else:
        print(f"Failed to create inherited process: {response.status_code}, {response.text}")
        return None, None
    
def main():
    parser = argparse.ArgumentParser(description="Fetch project and process details from Azure DevOps.")
    parser.add_argument('--source-url', required=True, help="Source Server URL (e.g., https://<instance>/<collection>)")
    parser.add_argument('--project-name', required=True, help="Source Project Name")
    parser.add_argument('--source-pat', required=True, help="Source Personal Access Token (PAT)")
    args = parser.parse_args()

    source_url = args.source_url.rstrip('/')
    project_name = args.project_name
    personal_access_token = args.source_pat

    try:
        instance, collection = source_url.rsplit('/', 1)
    except ValueError:
        print("Invalid Source Server URL. Ensure it is in the format 'https://<instance>/<collection>'")
        return

    auth = HTTPBasicAuth('', personal_access_token)
    projects = get_projects(instance, collection, auth)
    processes = get_processes(instance, collection, auth)

    target_project = next((p for p in projects if p['name'].lower() == project_name.lower()), None)
    if not target_project:
        print(f"Project '{project_name}' not found.")
        return

    project_id = target_project['id']
    properties = get_project_properties(instance, collection, project_id, auth)
    process_template_id = next((p['value'] for p in properties if p['name'] == "System.ProcessTemplateType"), None)
    if not process_template_id:
        print(f"Process template type not found for project '{project_name}'.")
        return

    process = find_process(processes, process_template_id)
    if not process:
        print(f"Process not found for template ID '{process_template_id}'.")
        return

    process_name = process['name']
    process_id = process['typeId']
    system_processes = ["Basic", "Agile", "Scrum", "CMMI"]

    if process_name in system_processes:
        new_process_id, new_process_name = create_inherited_process(instance, collection, auth, process_name, process_id)
        if new_process_id:
            print(f"Process Type - System")
            print(f"Process Name - {new_process_name}")
        else:
            print("Failed to create a custom inherited process.")
    else:
        print(f"Process Type - Inherited/Custom")
        print(f"Process Name - {process_name}")

if __name__ == "__main__":
    main()
