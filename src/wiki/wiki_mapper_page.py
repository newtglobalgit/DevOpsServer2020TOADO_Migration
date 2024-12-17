import os
from datetime import datetime
import openpyxl
import tempfile
import shutil
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
import time
import subprocess
import pytz
import sys
from wiki_comments_discover import get_wiki_comments, get_page_id
from wiki_migrate_comments import add_comment_to_wiki_page
import pandas as pd

# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.wiki.wiki_target_db import db_post_wiki
from src.wiki.wiki_target_db import db_get_wiki
from wiki_migrate_get_db import db_get_wiki
db_get_wiki()


def encode_url_component(component):
    return quote(component, safe='')


def get_last_modified_date_from_git(file_path, repo_dir):
    try:
        command = ["git", "log", "-1", "--format=%cd", file_path]
        result = subprocess.run(command, cwd=repo_dir, capture_output=True, text=True)
        if result.returncode == 0:
            commit_date_str = result.stdout.strip()
            last_modified = datetime.strptime(commit_date_str, "%a %b %d %H:%M:%S %Y %z")
            ist = pytz.timezone('Asia/Kolkata')
            last_modified = last_modified.astimezone(ist)
            return last_modified.strftime('%Y-%m-%d %H:%M:%S')
        else:
            print(f"Error fetching last commit date for {file_path}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error executing git log for {file_path}: {e}")
        return None


def clone_wiki_repo(auth_clone_url):
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"Cloning repository from {auth_clone_url} into {temp_dir}...")
        command = f"git clone {auth_clone_url} {temp_dir}"
        process = os.popen(command)
        output = process.read()
        process.close()
        if "fatal:" in output or "error:" in output:
            print(f"Error during git clone: {output}")
            return None
        else:
            print(f"Repository successfully cloned into {temp_dir}")
            return temp_dir
    except Exception as e:
        print(f"Error during git clone: {e}")
        return None


def discover_wiki_pages(wiki_repo_path):
    markdown_files = []
    for root, _, files in os.walk(wiki_repo_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, wiki_repo_path)
                last_modified = get_last_modified_date_from_git(relative_path, wiki_repo_path)
                if last_modified:
                    file_size = os.path.getsize(file_path)
                    markdown_files.append((relative_path, file_size, last_modified))
    return markdown_files


def handle_remove_readonly(func, path, excinfo):
    try:
        os.chmod(path, 0o777)
        func(path)
    except Exception as e:
        print(f"Error removing {path}: {e}")


def write_to_excel(data, output_file):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Wiki Discovery"
    
    # Define the headers
    headers = ["Project Name", "File Path", "Size (Bytes)", "Last Modified"]
    ws.append(headers)
    
    # Write the data
    for row in data:
        ws.append(row)
    
    # Save the workbook
    wb.save(output_file)
    print(f"Data successfully written to {output_file}")

def get_project_and_wiki_id(server_url, project_name, username, password):
    # Construct the full API URL
    api_url = f"{server_url}/{project_name}/_apis/wiki/wikis/{project_name}_wiki?api-version=6.0"
    
    # Send a GET request to the API with basic authentication
    response = requests.get(api_url, auth=HTTPBasicAuth(username, password))
    
    if response.status_code == 200:
        data = response.json()
        project_id = data.get('projectId')
        wiki_id = data.get('id')
        
        return project_id, wiki_id
    else:
        print(f"Error: Unable to fetch data (Status code: {response.status_code})")
        return None, None

def main():

    input_df = pd.read_excel("wiki_migrate_input.xlsx")
    input_df = input_df[['target_organization_url', 'target_project_name', 'target_pat']]
    source_df = pd.read_excel("wiki_source_discovery_reports.xlsx", sheet_name="Comments")
    target_df = pd.read_excel("wiki_target_discovery_reports.xlsx", sheet_name="Sheet")
    merged_df = pd.merge(
        source_df,
        target_df,
        on=['Project Name', 'File Path'],
        how='inner'  # Use inner join to get only matching records
    )

    merged_df = pd.merge(merged_df, input_df,  left_on=['Project Name'],
    right_on=['target_project_name']
    )

    for index, row in merged_df.iterrows():
        comment_text = row['Comment Text']

        org_url = row['target_organization_url']
        project_id = row['Project ID']
        wiki_id = row['Wiki ID']
        page_id = row['Page ID']
        pat = row['target_pat']
        comment_text = row['Comment Text']
        add_comment_to_wiki_page(org_url, project_id, wiki_id, page_id, pat,comment_text)

   

if __name__ == "__main__":
    main()
