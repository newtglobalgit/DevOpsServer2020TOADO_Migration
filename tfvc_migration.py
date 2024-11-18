import os
import requests
import base64
import tempfile
import urllib.parse
import shutil
import json
import pandas as pd

# Load the Excel file
file_path = 'migration_input_form.xlsx'  # Assuming the file is in the same directory as the script
source_df = pd.read_excel(file_path, sheet_name='source_migrate_input')
target_df = pd.read_excel(file_path, sheet_name='target_migrate_input')

# Remove leading/trailing spaces from column names and values
source_df.columns = source_df.columns.str.strip()
target_df.columns = target_df.columns.str.strip()
source_df = source_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
target_df = target_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Print column names and first row for verification
print("Source Columns:", source_df.columns)
print("Source Data:", source_df.iloc[0])
print("Target Columns:", target_df.columns)
print("Target Data:", target_df.iloc[0])

# Read configuration from the Excel file
source_collection_url = source_df['Source Server URL'].iloc[0]
source_project_name = source_df['Source Project Name'].iloc[0]
source_pat = source_df['PAT'].iloc[0]

target_collection_url = target_df['Target Organization URL'].iloc[0]
target_project_name = target_df['Target Project Name'].iloc[0]
target_pat = target_df['PAT'].iloc[0]

# Print PAT values for debugging
print("Source PAT:", source_pat)
print("Target PAT:", target_pat)

source_tfvc_path = f'$/{source_project_name}'.strip()
target_tfvc_path = f'$/{target_project_name}'.strip()

def get_basic_auth_header(pat):
    return 'Basic ' + base64.b64encode(f':{pat}'.encode()).decode()

def get_changesets(source_collection_url, source_pat):
    url = f"{source_collection_url}/_apis/tfvc/changesets?api-version=6.0"
    headers = {'Authorization': get_basic_auth_header(source_pat)}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['value']

def get_changeset_changes(source_collection_url, changeset_id, source_pat):
    url = f"{source_collection_url}/_apis/tfvc/changesets/{changeset_id}/changes?api-version=6.0"
    headers = {'Authorization': get_basic_auth_header(source_pat)}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['value']

def download_changeset_files(source_collection_url, changeset_id, changes, source_pat, temp_dir, deleted_files):
    headers = {'Authorization': get_basic_auth_header(source_pat)}
    for change in changes:
        item_path = change['item']['path']
        # Check if the file belongs to the specified source project
        if not item_path.startswith(source_tfvc_path):
            continue
        relative_path = item_path[len(source_tfvc_path):].lstrip('/')
        if change['changeType'] == 'delete':
            deleted_files.add(relative_path)
            continue
        if relative_path in deleted_files:
            continue

        encoded_path = urllib.parse.quote(item_path)
        item_url = f"{source_collection_url}/_apis/tfvc/items?path={encoded_path}&versionDescriptor.version={changeset_id}&api-version=6.0"
        print(f"Attempting to download: {item_url}")
        response = requests.get(item_url, headers=headers)
        if response.status_code == 404:
            print(f"File not found: {item_path} (URL: {item_url})")
            continue
        response.raise_for_status()
        file_path = os.path.join(temp_dir, relative_path)
        file_dir = os.path.dirname(file_path)
        # Ensure the directory structure exists
        if os.path.exists(file_dir) and not os.path.isdir(file_dir):
            os.remove(file_dir)
        os.makedirs(file_dir, exist_ok=True)
        # Handle file creation
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(response.content)
        else:
            print(f"File already exists: {file_path}")

def create_changeset(target_collection_url, target_pat, changes, comment):
    url = f"{target_collection_url}/_apis/tfvc/changesets?api-version=7.1-preview.3"
    headers = {
        'Authorization': get_basic_auth_header(target_pat),
        'Content-Type': 'application/json'
    }

    data = {
        "changes": changes,
        "comment": comment
    }

    print("Creating changeset with data:")
    print(json.dumps(data, indent=2))  # Debug print to check changes data

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code >= 400:
        print(f"Failed to create changeset. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    else:
        print(f"Successfully created changeset: {response.json()['changesetId']}")
        return response.json()['changesetId']

def file_exists_in_tfvc(target_collection_url, target_pat, path):
    url = f"{target_collection_url}/_apis/tfvc/items?path={urllib.parse.quote(path)}&api-version=6.0"
    headers = {'Authorization': get_basic_auth_header(target_pat)}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def upload_changeset_files(target_collection_url, target_pat, temp_dir, target_tfvc_path, deleted_files):
    changes = []
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, temp_dir).replace("\\", "/")
            if relative_path in deleted_files:
                continue
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            server_path = os.path.join(target_tfvc_path, relative_path).replace("\\", "/")

            if file_exists_in_tfvc(target_collection_url, target_pat, server_path):
                change_type = "edit"
            else:
                change_type = "add"

            changes.append({
                "changeType": change_type,
                "item": {
                    "path": server_path,
                    "contentMetadata": {
                        "encoding": -1  # -1 for binary files, use appropriate encoding for text files
                    }
                },
                "newContent": {
                    "content": content,
                    "contentType": "base64encoded"
                }
            })

    if not changes:
        print("No changes to upload.")
        return None

    comment = "Migrated from source TFVC"
    changeset_id = create_changeset(target_collection_url, target_pat, changes, comment)
    return changeset_id

def migrate_tfvc_to_tfvc(source_pat, source_collection_url, source_project_name, source_tfvc_path, target_pat, target_collection_url, target_project_name, target_tfvc_path):
    temp_dir = os.path.join(tempfile.gettempdir(), 'tfvc_migration')
    deleted_files = set()  # Track deleted files
    # Clean the temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Get changesets from source
    changesets = get_changesets(source_collection_url, source_pat)
    
    # Process each changeset
    for changeset in changesets:
        changeset_id = changeset['changesetId']
        print(f"Processing changeset {changeset_id}")
        changes = get_changeset_changes(source_collection_url, changeset_id, source_pat)
        download_changeset_files(source_collection_url, changeset_id, changes, source_pat, temp_dir, deleted_files)
    
    # Upload files to target
    changeset_id = upload_changeset_files(target_collection_url, target_pat, temp_dir, target_tfvc_path, deleted_files)
    print(f"Uploaded TFVC repository from {temp_dir} to {target_tfvc_path}. Created changeset {changeset_id}")

# Run the migration
migrate_tfvc_to_tfvc(source_pat, source_collection_url, source_project_name, source_tfvc_path, target_pat, target_collection_url, target_project_name, target_tfvc_path)
