import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
import subprocess
import time

# Load the Excel file and strip whitespace from headers
file_path = 'migration_input.xlsx'
data = pd.read_excel(file_path)
data.columns = data.columns.str.strip()  # Remove leading/trailing spaces from column names

# Verify necessary columns exist
required_columns = {'Source Project Name', 'Source PAT', 'Source Server URL', 'Target PAT', 'Target Organization URL'}
if not required_columns.issubset(data.columns):
    print("Error: Required columns are missing in the Excel file.")
    exit()

# Store the process template ID
process_template_id = None

# Function to print professional headers
def print_header(message):
    print(f"\n{'*' * 60}")
    print(f"{message.center(60)}")
    print(f"{'*' * 60}\n")

# Function to retrieve the process template ID
def get_process_template_id(organization_url, pat, source_process_name):
    url = f"{organization_url}/_apis/work/processes?api-version=7.1"
    response = requests.get(url, auth=HTTPBasicAuth('', pat))
    if response.status_code == 200:
        for process in response.json().get('value', []):
            if process.get('name') == source_process_name:
                return process.get('typeId')
    return None

# Function to check if the project exists
def check_project_exists(organization_url, project_name, pat):
    url = f"{organization_url}/_apis/projects?api-version=7.1"
    response = requests.get(url, auth=HTTPBasicAuth('', pat))
    if response.status_code == 200:
        projects = response.json().get('value', [])
        for project in projects:
            if project.get('name') == project_name:
                return True, project.get('id')
    return False, None

# Function to create a new project
def create_project(organization_url, project_name, process_template_id, pat):
    url = f"{organization_url}/_apis/projects?api-version=7.1"
    payload = {
        "name": project_name,
        "description": "Auto-created project for migration",
        "capabilities": {
            "versioncontrol": {
                "sourceControlType": "Git"
            },
            "processTemplate": {
                "templateTypeId": process_template_id
            }
        }
    }
    response = requests.post(url, json=payload, auth=HTTPBasicAuth('', pat))
    if response.status_code == 202:
        return True, response.json().get('id')
    return False, None

# Function to run process_finder.py
def get_source_process_name(source_url, project_name, source_pat):
    try:
        command = [
            "python", "process_finder.py",
            "--source-url", source_url,
            "--project-name", project_name,
            "--source-pat", source_pat
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split("\n")
        for line in output_lines:
            if line.startswith("Process Name - "):
                return line.split(" - ", 1)[-1].strip()
        return None
    except subprocess.CalledProcessError:
        return None

# Function to run process_migrate.py
def run_process_migration(source_url, source_pat, target_url, target_pat, source_process_name):
    try:
        command = [
            "python", "process_migrate.py",
            "--source-account-url", source_url,
            "--source-account-token", source_pat,
            "--target-account-url", target_url,
            "--target-account-token", target_pat,
            "--source-process-name", source_process_name
        ]
        # Removed the print statement that logs the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return "Successfully migrated process to target."
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else e.output.strip()
        if "Process with same name already exists on target account" in error_message:
            return "Process with the same name already exists on target account. Skipping migration."
        if not error_message:
            error_message = "Unknown error occurred during migration."
        return f"Error during migration: {error_message}"

# Main logic
for index, row in data.iterrows():
    print_header(f"Validating Row {index + 1}")
    
    source_url = str(row['Source Server URL']).strip()
    source_pat = str(row['Source PAT']).strip()
    target_url = str(row['Target Organization URL']).strip()
    target_pat = str(row['Target PAT']).strip()
    project_name = str(row['Source Project Name']).strip()
    target_project_name = row['Target Project Name'] if pd.notna(row.get('Target Project Name')) else project_name
    
    print(f"Source Project Name : {project_name}")
    
    # Step 1: Run process_finder.py to get Source Process Name
    source_process_name = get_source_process_name(source_url, project_name, source_pat)
    if source_process_name:
        print(f"Source Process Name : {source_process_name}")
    else:
        print(f"Source Process Name : Not found. Skipping row.\n")
        continue

    # Step 2: Run process_migrate.py
    migration_message = run_process_migration(source_url, source_pat, target_url, target_pat, source_process_name)
    print(f"Migrating Process    : {migration_message}")

    # Step 3: Retrieve process template ID
    if not process_template_id:
        process_template_id = get_process_template_id(target_url, target_pat, source_process_name)
        if not process_template_id:
            print(f"Error: Failed to retrieve process template ID. Skipping row.\n")
            continue

    # Step 4: Check if Target Project exists and create if not
    print("\nCreating Project in Target...")
    project_exists, project_id = check_project_exists(target_url, target_project_name, target_pat)
    if project_exists:
        print(f"Project '{target_project_name}' exists.\n")
    else:
        project_created, project_id = create_project(target_url, target_project_name, process_template_id, target_pat)
        if project_created:
            print(f"Project '{target_project_name}' creation initiated.\n")
        else:
            print(f"Error: Failed to create project '{target_project_name}'. Skipping row.\n")
            continue

        time.sleep(10)  # Allow time for project creation

        # Recheck if the project now exists
        project_exists, project_id = check_project_exists(target_url, target_project_name, target_pat)
        if project_exists:
            print(f"Project '{target_project_name}' exists after rechecking.\n")
        else:
            print(f"Error: Project '{target_project_name}' still not accessible. Skipping row.\n")
            continue

# Final footer
print_header("********** Pre-Migration Process Completed **********")
