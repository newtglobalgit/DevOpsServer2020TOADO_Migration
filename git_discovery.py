import os
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from datetime import datetime
import getpass
import logging
from collections import defaultdict
from utils.common import get_project_names, get_repo_names_by_project

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read configuration from Excel file
def read_config_from_excel(file_path):
    logging.info("Starting to read configuration from the Excel file.")
    try:
        df = pd.read_excel(file_path, sheet_name='Input')
        logging.info("Excel file loaded successfully.")
        logging.debug(f"DataFrame content:\n{df}")
    except FileNotFoundError:
        logging.error(f"The file '{file_path}' was not found.")
        return None, None, None, None, None, None
    except ValueError as e:
        logging.error(f"Failed to read the Excel file '{file_path}': {e}")
        return None, None, None, None, None, None
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading the Excel file: {e}")
        return None, None, None, None, None, None

    # Retrieve values from DataFrame
    try:
        server_url = df.at[0, 'Server URL'].strip()
        project = df.at[0, 'Project Name'].strip()
        pat = df.at[0, 'PAT'].strip()
        repository_name = df.at[0, 'Repository Name'].strip()
        branch_name = df.at[0, 'Branch Name'].strip() if not pd.isna(df.at[0, 'Branch Name']) else None
    except KeyError as e:
        logging.error(f"Missing required column in the Excel file: {e}")
        return None, None, None, None, None, None
    except Exception as e:
        logging.error(f"An unexpected error occurred while retrieving configuration data: {e}")
        return None, None, None, None, None, None

    # Check if required fields are present
    if not server_url or not project or not pat or not repository_name:
        logging.warning("Some required data (Server URL, Project, PAT, Repository Name) is missing in the Excel file.")
        return None, None, None, None, None, None

    logging.info("Configuration successfully read from the Excel file.")
    return server_url, project, pat, repository_name, branch_name, df


def authenticate_and_get_projects(server_url, pat, api_version):
    logging.info(f"Attempting to authenticate with the server at {server_url}")
    auth = HTTPBasicAuth('', pat)
    try:
        response = requests.get(f'{server_url}/_apis/projects?api-version={api_version}', auth=auth)
        response.raise_for_status()
        logging.info("Authentication successful.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error during authentication: {e}")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error during authentication to server '{server_url}': {e}")
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout error during authentication to server '{server_url}': {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during authentication: {e}")
    return None


def get_repositories(server_url, project, pat, api_version):
    logging.info(f"Fetching repositories for project '{project}' on server '{server_url}'")
    auth = HTTPBasicAuth('', pat)
    repos_url = f'{server_url}/{project}/_apis/git/repositories?api-version={api_version}'
    try:
        response = requests.get(repos_url, auth=auth)
        response.raise_for_status()
        logging.info(f"Successfully retrieved repositories for project '{project}'")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error while retrieving repositories for project '{project}': {e}")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error while retrieving repositories for project '{project}': {e}")
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout error while retrieving repositories for project '{project}': {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"General error while retrieving repositories for project '{project}': {e}")
    return None


def get_branches(server_url, project, repository_id, pat, api_version):
    logging.info(f"Fetching branches for repository ID '{repository_id}' in project '{project}'")
    auth = HTTPBasicAuth('', pat)
    branches_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/refs?filter=heads&api-version={api_version}'
    try:
        response = requests.get(branches_url, auth=auth)
        response.raise_for_status()
        logging.info(f"Successfully retrieved branches for repository ID '{repository_id}'")
        return response.json()['value']
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error while retrieving branches for repository ID '{repository_id}': {e}")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error while retrieving branches for repository ID '{repository_id}': {e}")
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout error while retrieving branches for repository ID '{repository_id}': {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"General error while retrieving branches for repository ID '{repository_id}': {e}")
    return None


def get_latest_commit_info(server_url, project, repository_id, branch_name, pat, api_version):
    logging.info(f"Fetching latest commit information for branch '{branch_name}' in repository ID '{repository_id}'")
    auth = HTTPBasicAuth('', pat)
    commits_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/commits?searchCriteria.itemVersion.version={branch_name}&$top=1&api-version={api_version}'
    try:
        response = requests.get(commits_url, auth=auth)
        response.raise_for_status()
        commit = response.json()['value'][0]
        logging.info(f"Successfully retrieved latest commit for branch '{branch_name}'")
        return commit['commitId'], commit['comment'], commit['author']['name'], commit['author']['date']
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve latest commit for branch '{branch_name}': {e}")
    except IndexError:
        logging.warning(f"No commits found for branch '{branch_name}' in repository '{repository_id}'")
    except KeyError as e:
        logging.error(f"Unexpected response format while fetching latest commit: {e}")
    return None, None, None, None


def get_files_in_branch(server_url, project, repository_id, branch_name, pat, api_version):
    logging.info(f"Retrieving files in branch '{branch_name}' for repository ID '{repository_id}'")
    auth = HTTPBasicAuth('', pat)
    items_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/items?scopePath=/&recursionLevel=Full&versionDescriptor[version]={branch_name}&api-version={api_version}'
    try:
        response = requests.get(items_url, auth=auth)
        response.raise_for_status()
        logging.info(f"Successfully retrieved files in branch '{branch_name}'")
        return response.json()['value']
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve files in branch '{branch_name}': {e}")
    except KeyError as e:
        logging.error(f"Unexpected response format while retrieving files: {e}")
    return None


def get_commit_count(server_url, project, repository_id, file_path, pat, api_version):
    logging.info(f"Calculating commit count for file '{file_path}' in repository ID '{repository_id}'")
    auth = HTTPBasicAuth('', pat)
    commits_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/commits?searchCriteria.itemPath={file_path}&api-version={api_version}'
    try:
        response = requests.get(commits_url, auth=auth)
        response.raise_for_status()
        commit_count = response.json()['count']
        logging.info(f"Commit count for file '{file_path}': {commit_count}")
        return max(commit_count, 1)  # Ensure at least one commit
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve commit count for file '{file_path}': {e}")
    except KeyError as e:
        logging.error(f"Unexpected response format while calculating commit count: {e}")
    return 1  # Assume at least one commit if there's an error


def process(server_url, pat, project, repository_name, branch_name):
    api_version = '6.0'  # Change this if your server uses a different version
    logging.info(f"Starting process for server '{server_url}', project '{project}', repository '{repository_name}', branch '{branch_name}'")

    # Authenticate and get projects (optional step to confirm login)
    projects = authenticate_and_get_projects(server_url, pat, api_version)
    if not projects:
        logging.error("Authentication or project retrieval failed. Exiting process.")
        return [], [], [], []

    repositories = get_repositories(server_url, project, pat, api_version)
    if not repositories:
        logging.error("Failed to retrieve repositories. Exiting process.")
        return [], [], [], []

    for repo in repositories['value']:
        if repo['name'] == repository_name:
            repo_id = repo['id']
            logging.info(f"Matched repository '{repository_name}' with ID '{repo_id}'")

            data_source_code = []
            data_commits = []
            data_all_commits = []
            data_tags = []

            branches = get_branches(server_url, project, repo_id, pat, api_version)
            if branches:
                branch_names = [branch['name'].replace('refs/heads/', '') for branch in branches] if branch_name is None else [branch_name]
                for branch in branch_names:
                    logging.info(f"Processing branch '{branch}' in repository '{repository_name}'")
                    commit_id, comment, author, last_modified = get_latest_commit_info(server_url, project, repo_id, branch, pat, api_version)
                    if commit_id:
                        logging.debug(f"Latest commit ID '{commit_id}' in branch '{branch}'")

                        commits = get_all_commits(server_url, project, repo_id, branch, pat, api_version)
                        for commit in commits:
                            commit_info = {
                                'Collection Name': server_url.split('/')[-1],
                                'Project Name': project,
                                'Repository Name': repository_name,
                                'Branch Name': branch,
                                'Commit ID': commit['commitId'],
                                'Commit Message': commit['comment'],
                                'Author': commit['author']['name'],
                                'Commit Date': commit['author']['date']
                            }
                            data_commits.append(commit_info)

                        files = get_files_in_branch(server_url, project, repo_id, branch, pat, api_version)
                        if files:
                            for file in files:
                                logging.debug(f"Analyzing file '{file['path']}' in branch '{branch}'")
                                is_folder = file.get('isFolder', file['gitObjectType'] == 'tree')
                                if not is_folder:
                                    sha1 = file['objectId']
                                    size = get_file_size(server_url, project, repo_id, sha1, pat, api_version)
                                    commit_count = get_commit_count(server_url, project, repo_id, file['path'], pat, api_version)
                                else:
                                    size = 0
                                    commit_count = 0
                                file_info = {
                                    'Collection Name': server_url.split('/')[-1],
                                    'Project Name': project,
                                    'Repository Name': repository_name,
                                    'Branch Name': branch,
                                    'File Name': file['path'].split('/')[-1],
                                    'File Type': 'Folder' if is_folder else 'File',
                                    'Folder Level': file['path'].count('/') - 1,
                                    'Path': file['path'],
                                    'Size (Bytes)': int(size),
                                    'Last Modified Time': last_modified,
                                    'Author': author,
                                    'Comments': comment,
                                    'Commit ID': commit_id,
                                    'Commit Count': commit_count
                                }
                                data_source_code.append(file_info)

            logging.info(f"Process completed for repository '{repository_name}' in project '{project}'")
            return data_source_code, data_commits, [], []

    logging.warning("Specified repository not found in the project. Process terminated.")
    return [], [], [], []
