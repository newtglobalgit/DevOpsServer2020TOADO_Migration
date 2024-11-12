import os
import re
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import getpass
import time
import shutil
import subprocess
import logging
from utils.common import get_project_names, add_if_not_exists
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

# Set up logging directory and configuration
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(log_dir, f'tfvc_discovery_{datetime.now().strftime("%Y%m%d%H%M%S")}.log'))
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def modify_item_path(url):
    try:
        replacements = {
            '+': '%2B', '%24': '$', '&': '%26', ',': '%2C', ':': '%3A',
            ';': '%3B', '=': '%3D', '?': '%3F', '@': '%40', ' ': '%20',
            '"': '%22', '<': '%3C', '>': '%3E', '#': '%23', '{': '%7B',
            '}': '%7D', '|': '%7C', '\\': '%5C', '^': '%5E', '[': '%5B',
            ']': '%5D', '`': '%60'
        }
        pattern = r"itemPath=(.+?)&api-version"
        match = re.search(pattern, url)
        
        if match:
            item_path = match.group(1)
            logger.info(f"Original item path: {item_path}")
            for char, replacement in replacements.items():
                item_path = item_path.replace(char, replacement)
            modified_url = url.replace(match.group(1), item_path)
            logger.info(f"Modified item path: {item_path}")
            return modified_url
        return url
    except Exception as e:
        logger.error(f"Failed to modify item path: {e}")
        return url

def make_request_with_retries(url, auth, max_retries=10, timeout=300):
    url = modify_item_path(url)
    logger.info(f"Making request to URL: {url}")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, auth=auth, timeout=timeout)
            if response.status_code == 200:
                logger.info(f"Request successful with status code: {response.status_code}")
                return response
            else:
                logger.warning(f"Attempt {attempt + 1}: Request timed out. Retrying...")
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Error during request: {e}")
            break
    logger.error(f"Failed to connect after {max_retries} attempts.")
    return None

def get_shelvesets_details(server_url, pat):
    try:
        url = f"{server_url}/_apis/tfvc/shelvesets?api-version=6.0"
        response = make_request_with_retries(url, auth=HTTPBasicAuth('', pat))
        return response.json().get('value', []) if response else []
    except Exception as e:
        logger.error(f"Failed to retrieve shelvesets: {e}")
        return []
    
def get_all_branches(server_url, project_name, pat):
    """
    Gets all branches from the Azure DevOps TFVC server.

    Parameters:
    - server_url: str, URL of the Azure DevOps server
    - project_name: str, name of the project to get branches from
    - pat: str, personal access token for authentication

    Returns:
    - list of branch paths
    """
    logger.info(f"Getting all branches for project '{project_name}' from {server_url}")
    branches = []
    url = f"{server_url}/{project_name}/_apis/tfvc/branches?api-version=6.0"
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth('', pat))
        
        if response.status_code == 200:
            branch_data = response.json().get('value', [])
            branches = [branch.get('path', 'Unnamed Branch') for branch in branch_data]
            logger.info(f"Found {len(branches)} branches.")
        else:
            logger.error(f"Failed to retrieve branches. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error occurred while retrieving branches: {e}")
    
    return branches

def file_discovery(root_folder, branches):
    """
    Discovers all files and folders in the specified root folder and returns their details as a DataFrame.

    Parameters:
    - root_folder: str, path of the folder to discover files and folders in
    - branches: list, list of branch paths

    Returns:
    - DataFrame with details of discovered files and folders
    """
    try:
        logger.info(f"Starting file discovery in folder: {root_folder}")
        file_details = []

        for dirpath, dirnames, filenames in os.walk(root_folder):
            root_folder_name = os.path.basename(root_folder)
            project_folder_name = os.path.relpath(dirpath, root_folder)
            is_branch = "Yes" if dirpath in branches else "No"

            # Add folder details
            for dirname in dirnames:
                folder_path = os.path.join(dirpath, dirname)
                file_details.append([
                    root_folder_name,
                    project_folder_name,
                    dirname,
                    "Folder",
                    "",  # File size is not applicable for folders
                    folder_path,
                    is_branch
                ])

            # Add file details
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                file_size = os.path.getsize(file_path)
                file_type = os.path.splitext(filename)[1]

                file_details.append([
                    root_folder_name,
                    project_folder_name,
                    filename,
                    'File',
                    file_size,
                    file_path,
                    is_branch
                ])

        # Create a DataFrame and return
        df = pd.DataFrame(file_details, columns=[
            "Root Folder", "Project Folder", "Name", "Type", "File Size (bytes)", "Path", "Is Branch"
        ])
        
        logger.info("File and folder discovery completed successfully.")
        return df
    except Exception as e:
        logger.error("Error during file and folder discovery.")
        logger.exception(e)

def generate_excel_report(output_dir, server_url, pat, project, start_time, local_clone_path):
    try:
        project_name = project
        collection_name = server_url.split('/')[-1]
        branch_data = []
        all_changesets_data = []
        all_shelvesets_data = []

        # Fetch branches
        tfvc_check_api_url = f'{server_url}/{project_name}/_apis/tfvc/branches?api-version=6.0'
        tfvc_response = make_request_with_retries(tfvc_check_api_url, auth=HTTPBasicAuth('', pat))
        if tfvc_response and tfvc_response.status_code == 200:
            tfvc_branches = tfvc_response.json()['value']
            for tfvc_branch in tfvc_branches:
                branch_path = tfvc_branch.get('path', 'Unnamed Branch')
                branch_name = branch_path.split('/')[-1]
                branch_data.append({
                    'Collection Name': collection_name,
                    'Project Name': project_name,
                    'Repository Name': 'TFVC',
                    'Branch Name': branch_name,
                })
        else:
            logger.error(f"Failed to retrieve TFVC branches for project '{project_name}'. Status code: {tfvc_response.status_code}")

        # Fetch changesets
        changeset_url = f"{server_url}/{project_name}/_apis/tfvc/changesets?api-version=6.0&$top=10000"
        changeset_response = make_request_with_retries(changeset_url, auth=HTTPBasicAuth('', pat))
        if changeset_response and changeset_response.status_code == 200:
            for changeset in changeset_response.json().get('value', []):
                all_changesets_data.append({
                    'Collection Name': collection_name,
                    'Project Name': project_name,
                    'Changeset ID': changeset['changesetId'],
                    'Author': changeset['author']['displayName'],
                    'Time Date': changeset['createdDate'],
                    'Comment': changeset.get('comment', 'No comment')
                })
        else:
            logger.error(f"Failed to retrieve changesets for project '{project_name}'. Status code: {changeset_response.status_code}")

        # Fetch shelvesets
        shelvesets = get_shelvesets_details(server_url, pat)
        for shelveset in shelvesets:
            shelveset_name, shelveset_id = shelveset['id'].split(';', 1)
            all_shelvesets_data.append({
                'Collection Name': collection_name,
                'Project Name': project_name,
                'Shelveset Name': shelveset_name,
                'Shelveset ID': shelveset_id,
                'Author': shelveset['owner']['displayName'],
                'Created Date': shelveset['createdDate'],
                'Comment': shelveset.get('comment', 'No comment')
            })

        # Start creating the Excel report
        excel_output_path = os.path.join(output_dir, f"{project_name}_{collection_name}_tfvc_discovery_report.xlsx")

        # Helper function for writing formatted sheets with borders and zoom
        def write_formatted_sheet(writer, df, sheet_name):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.hide_gridlines(2)
            worksheet.set_column(0, len(df.columns) - 1, 30)
            worksheet.set_zoom(70)  # Set the zoom level to 70%
            for col_num, value in enumerate(df.columns):
                worksheet.write(0, col_num, value, header_format)

            # Apply borders to all cells
            for row_num in range(1, len(df) + 1):
                for col_num, value in enumerate(df.iloc[row_num - 1]):
                    cell_format = bordered_format if len(str(value)) > 30 else bordered_format
                    worksheet.write(row_num, col_num, value, cell_format)

        with pd.ExcelWriter(excel_output_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#000080',
                'border': 1
            })
            wrap_format = workbook.add_format({'border': 1, 'text_wrap': True})
            bordered_format = workbook.add_format({'border': 1})  # Added bordered format for all cells

            # Summary sheet
            worksheet_summary = workbook.add_worksheet('Summary')
            worksheet_summary.hide_gridlines(2)
            worksheet_summary.set_zoom(70)  # Set zoom for summary sheet
            run_duration = datetime.now() - start_time
            formatted_run_duration = f"{int(run_duration.total_seconds() // 3600)} hours, {int(run_duration.total_seconds() % 3600 // 60)} minutes, {run_duration.total_seconds() % 60:.1f} seconds"

            summary_data = {
                'Report Title': f"Project {project_name} TFVC Report.",
                'Purpose of the report': f"This report provides a summary and detailed view of the TFVC in project {project_name}.",
                'Run Date': datetime.now().strftime('%d-%b-%Y %I:%M %p'),
                'Run Duration': formatted_run_duration,
                'Run By': getpass.getuser()
            }

            row = 0
            for key, value in summary_data.items():
                worksheet_summary.write(row, 0, key, header_format)
                worksheet_summary.write(row, 1, value, wrap_format if len(str(value)) > 30 else bordered_format)
                row += 1
            worksheet_summary.set_column(0, 0, 25.71)
            worksheet_summary.set_column(1, 1, 30)

            # Changeset Data
            changeset_df = pd.DataFrame(all_changesets_data)
            write_formatted_sheet(writer, changeset_df, 'Changesets')

            # Shelveset Data
            shelveset_df = pd.DataFrame(all_shelvesets_data)
            write_formatted_sheet(writer, shelveset_df, 'Shelvesets')

            # File Discovery Data
            branches = get_all_branches(server_url, project_name, pat)
            file_discovery_df = file_discovery(local_clone_path, branches)
            write_formatted_sheet(writer, file_discovery_df, 'File_Discovery')
            logger.info("File discovery details added to Excel report.")

        logger.info(f"Report saved to {excel_output_path}")
    except Exception as e:
        logger.error(f"Failed to generate Excel report for project '{project}': {e}")

def clean_local_clone_path(local_clone_path):
    if os.path.exists(local_clone_path):
        logger.info(f"Cleaning up the existing clone folder at {local_clone_path}")
        shutil.rmtree(local_clone_path)
        logger.info("Clone folder cleaned up successfully.")
    os.makedirs(local_clone_path)

def clone_project_from_tfvc(surl, proj_name, username, password, local_clone_path):

    logger.info("Starting TFVC clone process...")
    clean_local_clone_path(local_clone_path)

    # Read the Excel file
    try:
        collection_url = surl
        project_name = proj_name

        logger.info(f"Collection URL: {collection_url}")
        logger.info(f"Project Name: {project_name}")
    except Exception as e:
        logger.error("Error reading the Excel file.")
        logger.exception(e)
        return

    # Authenticate with Azure DevOps
    try:
        logger.info("Authenticating with Azure DevOps...")
        credentials = BasicAuthentication(username, password)
        connection = Connection(base_url=collection_url, creds=credentials)
        logger.info("Authentication successful.")
    except Exception as e:
        logger.error("Authentication failed.")
        logger.exception(e)
        return

    # Use tf.exe to clone the project
    try:
        logger.info(f"Cloning project '{project_name}' to '{local_clone_path}'")

        # Delete existing workspace if it exists
        tf_workspace_exists_command = [
            "tf", "workspaces",
            f"/collection:{collection_url}",
            f"/login:{username},{password}"
        ]
        p0 = subprocess.run(tf_workspace_exists_command, capture_output=True, text=True)

        if "MyWorkspace" in p0.stdout:
            logger.info("Workspace 'MyWorkspace' already exists. Deleting it...")
            tf_delete_workspace_command = [
                "tf", "workspace", "/delete",
                "MyWorkspace",
                f"/collection:{collection_url}",
                f"/login:{username},{password}"
            ]
            p_delete = subprocess.run(tf_delete_workspace_command, capture_output=True, text=True)
            if p_delete.returncode != 0:
                logger.error("Failed to delete existing workspace.")
                logger.error(f"Error output: {p_delete.stderr}")
                return
            else:
                logger.info("Existing workspace deleted successfully.")

        # Create a new workspace
        tf_workspace_command = [
            "tf", "workspace", "-new",
            "MyWorkspace",
            f"/collection:{collection_url}",
            f"/login:{username},{password}"
        ]
        p1 = subprocess.run(tf_workspace_command, capture_output=True, text=True)

        if p1.returncode != 0:
            logger.error("Failed to create workspace.")
            logger.error(f"Error output: {p1.stderr}")
            return
        else:
            logger.info("Workspace created successfully.")

        # Map the project to the local directory
        tf_map_command = [
            "tf", "workfold", "/map",
            f"$/{project_name}", local_clone_path,
            f"/collection:{collection_url}",
            f"/login:{username},{password}"
        ]
        p2 = subprocess.run(tf_map_command, capture_output=True, text=True)

        if p2.returncode != 0:
            logger.error("Failed to map project to the local directory.")
            logger.error(f"Error output: {p2.stderr}")
            return
        else:
            logger.info("Project mapped to the local directory successfully.")

        # Perform the get command to download files
        tf_get_command = [
            "tf", "get", f"$/{project_name}", "/recursive",
        ]
        process = subprocess.run(tf_get_command, capture_output=True, text=True)

        if process.returncode == 0:
            logger.info("Project cloned successfully.")
        else:
            logger.error("Failed to clone the project.")
            logger.error(f"Error output: {process.stderr}")
            return

    except Exception as e:
        logger.error("An error occurred during the TFVC clone process.")
        logger.exception(e)
        return


def main():
    cwd = os.getcwd()
    input_file = os.path.join(cwd, 'tfvc_discovery_input_form.xlsx')
    local_clone_path = os.path.join(cwd, 'clone')

    try:
        run_id = str(int(datetime.now().strftime("%Y%m%d%H%M%S")))
        output_directory = os.path.join("TFVC", run_id)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        df = pd.read_excel(input_file)
        df['Server URL'] = df['Server URL'].str.strip().fillna('')
        df['Project Name'] = df['Project Name'].str.strip().fillna('')
        df['PAT'] = df['PAT'].str.strip().fillna('')

        input_data = {}
        for index, row in df.iterrows():
            if pd.isna(row['Server URL']) or pd.isna(row['PAT']):
                print(f"Skipping row {int(index) + 1} due to missing data. ServerURL and PAT values are mandatory.")
                continue
            surl = row['Server URL']
            if surl.endswith('/'):
                surl = surl.rstrip('/')
            proj_name = row['Project Name']
            ptoken = row['PAT']
            username = row['Username']
            password = row['Password']
            proj_names = []
            clone_project_from_tfvc(surl, proj_name, username, password, local_clone_path)
            if not proj_name:
                proj_names = get_project_names(devops_server_url=surl, pat=ptoken)
            if surl not in input_data:
                input_data[surl] = {"pat": ptoken, "projects": [proj_name] if proj_name else proj_names}
            else:
                add_if_not_exists(input_data[surl]["projects"], [proj_name] if proj_name else proj_names)

        for server_url in input_data:
            pat = input_data[server_url]["pat"]
            for project in input_data[server_url]["projects"]:
                start_time = datetime.now()
                try:
                    generate_excel_report(output_directory, server_url, pat, project, start_time, local_clone_path)
                except Exception as e:
                    logger.error(f"Error occurred while processing project '{project}': {e}")
    except Exception as e:
        logger.error(f"Error occurred while processing input file '{input_file}': {e}")

if __name__ == "__main__":
    main()
