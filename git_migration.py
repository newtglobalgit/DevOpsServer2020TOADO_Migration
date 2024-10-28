import os
import subprocess
import sys
import pandas as pd
from datetime import datetime

# Function to execute shell commands
def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}\n{result.stderr}")
        sys.exit(1)
    print(result.stdout)

# Read the Excel file
input_file = r'migration_input_form.xlsx'

# Read source and target inputs
source_df = pd.read_excel(input_file, sheet_name='source_migrate_input')
target_df = pd.read_excel(input_file, sheet_name='target_migrate_input')

# Trim whitespace from column names
source_df.columns = source_df.columns.str.strip()
target_df.columns = target_df.columns.str.strip()

# Print actual column names read from the Excel file
print("Source sheet columns:", source_df.columns.tolist())
print("Target sheet columns:", target_df.columns.tolist())

# Validate input data
required_columns_source = ['Source Server URL', 'Source Project Name', 'PAT', 'Source Repository Name']
required_columns_target = ['Target Organization URL', 'Target Project Name', 'PAT', 'Target Repository Name']

if not all(column in source_df.columns for column in required_columns_source):
    print(f"Source sheet is missing required columns: {required_columns_source}")
    sys.exit(1)

if not all(column in target_df.columns for column in required_columns_target):
    print(f"Target sheet is missing required columns: {required_columns_target}")
    sys.exit(1)

# Extract source and target information
source_server_url = source_df['Source Server URL'].iloc[0].strip()
source_project_name = source_df['Source Project Name'].iloc[0].strip()
source_pat = source_df['PAT'].iloc[0].strip()
source_repo_name = source_df['Source Repository Name'].iloc[0].strip()

target_org_url = target_df['Target Organization URL'].iloc[0].strip()
target_project_name = target_df['Target Project Name'].iloc[0].strip()
target_pat = target_df['PAT'].iloc[0].strip()
target_repo_name = target_df['Target Repository Name'].iloc[0].strip()

# Remove protocol from URLs if present
if source_server_url.startswith("http://"):
    source_server_url = source_server_url[7:]
elif source_server_url.startswith("https://"):
    source_server_url = source_server_url[8:]

if target_org_url.startswith("http://"):
    target_org_url = target_org_url[7:]
elif target_org_url.startswith("https://"):
    target_org_url = target_org_url[8:]

# Construct URLs with PAT
source_url_with_pat = f"http://{source_pat}@{source_server_url}/{source_project_name}/_git/{source_repo_name}"
target_url_with_pat = f"https://{target_pat}@{target_org_url}/{target_project_name}/_git/{target_repo_name}"

# Print URLs for debugging
print(f"Source URL: {source_url_with_pat}")
print(f"Target URL: {target_url_with_pat}")

# Add a timestamp to the directory name
timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
clone_dir = f"{source_repo_name}_{timestamp}.git"

# Clone the repository from Azure DevOps Server
print("Cloning repository from Azure DevOps Server...")
clone_command = f"git clone --mirror {source_url_with_pat} {clone_dir}"
run_command(clone_command)

# Navigate into the repository directory
os.chdir(clone_dir)

# Add new remote for Azure DevOps Services
print("Adding new remote for Azure DevOps Services...")
add_remote_command = f"git remote add new-origin {target_url_with_pat}"
run_command(add_remote_command)

# Push all branches and tags to the new remote
print("Pushing all branches and tags to Azure DevOps Services...")
push_command = "git push new-origin --mirror"
run_command(push_command)

print("Migration completed successfully.")
