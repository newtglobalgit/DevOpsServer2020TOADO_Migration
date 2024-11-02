import os
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from datetime import datetime
import getpass
from collections import defaultdict
from utils.common import get_project_names, get_repo_names_by_project


# Function to read configuration from Excel file
def read_config_from_excel(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name='Input')
        print("DataFrame loaded successfully.")
        print("DataFrame content:")
        print(df)
    except ValueError as e:
        print(f"Error: {e}")
        return None, None, None, None, None, None

    server_url = df.at[0, 'Server URL'].strip()
    project = df.at[0, 'Project Name'].strip()
    pat = df.at[0, 'PAT'].strip()
    repository_name = df.at[0, 'Repository Name'].strip()
    branch_name = df.at[0, 'Branch Name'].strip() if not pd.isna(df.at[0, 'Branch Name']) else None

    if not server_url or not project or not pat or not repository_name:
        print("Please ensure the Excel file contains the required data.")
        return None, None, None, None, None, None

    return server_url, project, pat, repository_name, branch_name, df


def authenticate_and_get_projects(server_url, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    try:
        response = requests.get(f'{server_url}/_apis/projects?api-version={api_version}', auth=auth)
        response.raise_for_status()
        print('Login successful.')
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Failed to authenticate: {e}')
        return None


def get_repositories(server_url, project, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    repos_url = f'{server_url}/{project}/_apis/git/repositories?api-version={api_version}'
    print(f"Requesting repositories with URL: {repos_url}")
    try:
        response = requests.get(repos_url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve repositories: {e}')
        return None


def get_branches(server_url, project, repository_id, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    branches_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/refs?filter=heads&api-version={api_version}'
    print(f"Requesting branches with URL: {branches_url}")
    try:
        response = requests.get(branches_url, auth=auth)
        response.raise_for_status()
        return response.json()['value']
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve branches: {e}')
        return None


def get_latest_commit_info(server_url, project, repository_id, branch_name, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    commits_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/commits?searchCriteria.itemVersion.' \
                  f'version={branch_name}&$top=1&api-version={api_version}'
    try:
        response = requests.get(commits_url, auth=auth)
        response.raise_for_status()
        commit = response.json()['value'][0]
        commit_id = commit['commitId']
        comment = commit['comment']
        author = commit['author']['name']
        last_modified = commit['author']['date']
        return commit_id, comment, author, last_modified
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve last commit: {e}')
        return None, None, None, None


def get_files_in_branch(server_url, project, repository_id, branch_name, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    items_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/items?scopePath=/&recursionLevel=' \
                f'Full&versionDescriptor[version]={branch_name}&api-version={api_version}'
    print(f"Requesting items with URL: {items_url}")
    try:
        response = requests.get(items_url, auth=auth)
        response.raise_for_status()
        return response.json()['value']
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve items in branch: {e}')
        return None


def get_file_size(server_url, project, repository_id, sha1, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    blob_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/blobs/{sha1}?api-version={api_version}'
    print(f"Requesting blob size with URL: {blob_url}")
    try:
        response = requests.get(blob_url, auth=auth)
        response.raise_for_status()
        return response.headers.get('Content-Length', 0)
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve blob size: {e}')
        return 0


def get_commit_count(server_url, project, repository_id, file_path, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    commits_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/commits?searchCriteria.' \
                  f'itemPath={file_path}&api-version={api_version}'
    print(f"Requesting commit count with URL: {commits_url}")
    try:
        response = requests.get(commits_url, auth=auth)
        response.raise_for_status()
        commit_count = response.json()['count']
        return max(commit_count, 1)  # Ensure at least one commit
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve commit count for {file_path}: {e}')
        return 1  # Assume at least one commit


def get_all_commits(server_url, project, repository_id, branch_name, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    commits_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/commits?searchCriteria.' \
                  f'itemVersion.version={branch_name}&api-version={api_version}'
    print(f"Requesting all commits with URL: {commits_url}")
    try:
        response = requests.get(commits_url, auth=auth)
        response.raise_for_status()
        return response.json()['value']
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve commits: {e}')
        return []


def get_all_repo_commits(server_url, project, repository_id, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    commits_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/commits?api-version={api_version}'
    print(f"Requesting all repository commits with URL: {commits_url}")
    try:
        response = requests.get(commits_url, auth=auth)
        response.raise_for_status()
        return response.json()['value']
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve all repository commits: {e}')
        return []


def get_tags(server_url, project, repository_id, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    tags_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/refs?filter=tags&api-version={api_version}'
    print(f"Requesting tags with URL: {tags_url}")
    try:
        response = requests.get(tags_url, auth=auth)
        response.raise_for_status()
        return response.json()['value']
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve tags: {e}')
        return []


def get_tag_details(server_url, project, repository_id, tag_id, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    tag_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/annotatedtags/{tag_id}?api-version=6.0-preview.1'
    try:
        response = requests.get(tag_url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve tag details for {tag_id}: {e}')
        return None


def get_commit_details(server_url, project, repository_id, commit_id, pat, api_version):
    auth = HTTPBasicAuth('', pat)
    commit_url = f'{server_url}/{project}/_apis/git/repositories/{repository_id}/commits/{commit_id}?api-version={api_version}'
    try:
        response = requests.get(commit_url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve commit details for {commit_id}: {e}')
        return None


def map_commit_tags(tags):
    commit_tag_map = {}
    for tag in tags:
        commit_id = tag['peeledObjectId'] if 'peeledObjectId' in tag else tag['objectId']
        commit_tag_map[commit_id] = tag['name']
    return commit_tag_map


def apply_header_styles(workbook, sheet_name):
    sheet = workbook[sheet_name]
    header_fill = PatternFill(start_color='000080', end_color='000080', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    for cell in sheet[1]:  # Assuming headers are in the first row
        cell.fill = header_fill
        cell.font = header_font


def apply_black_border(sheet):
    thin_border = Border(left=Side(style='thin', color='000000'),
                         right=Side(style='thin', color='000000'),
                         top=Side(style='thin', color='000000'),
                         bottom=Side(style='thin', color='000000'))
    for row in sheet.iter_rows():
        for cell in row:
            cell.border = thin_border


def remove_gridlines(sheet):
    sheet.sheet_view.showGridLines = False


def adjust_column_width(sheet):
    for column_cells in sheet.columns:
        max_length = 0
        column = column_cells[0].column_letter  # Get the column name
        for cell in column_cells:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length, 30)
        sheet.column_dimensions[column].width = adjusted_width


def align_cells(sheet):
    for row in sheet.iter_rows(min_row=2):  # Skip header row
        for cell in row:
            if isinstance(cell.value, (int, float)):
                cell.alignment = Alignment(horizontal='right')
            elif isinstance(cell.value, datetime) or isinstance(cell.value, str) and '-' in cell.value and ':' in cell.value:
                cell.alignment = Alignment(horizontal='right')
            else:
                cell.alignment = Alignment(horizontal='left')


def sanitize_sheet_name(name):
    invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name[:31]  # Excel sheet names can have a maximum of 31 characters


def generate_report(data_source_code, data_commits, data_all_commits, data_tags, output_path, project_name, config_df):
    start_time = datetime.now()
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Create an empty summary sheet
        pd.DataFrame().to_excel(writer, sheet_name='summary', index=False)
        df_source_code = pd.DataFrame(data_source_code)
        df_commits = pd.DataFrame(data_commits)
        df_all_commits = pd.DataFrame(data_all_commits)
        df_tags = pd.DataFrame(data_tags)
        df_source_code.to_excel(writer, sheet_name='source_code', index=False)
        df_commits.to_excel(writer, sheet_name='commits', index=False)
        df_tags.to_excel(writer, sheet_name='tags', index=False)
    
    workbook = load_workbook(output_path)
    worksheet_summary = workbook['summary']
    apply_header_styles(workbook, 'source_code')
    apply_header_styles(workbook, 'commits')
    apply_header_styles(workbook, 'tags')

    apply_black_border(workbook['summary'])
    apply_black_border(workbook['source_code'])
    apply_black_border(workbook['commits'])
    apply_black_border(workbook['tags'])

    remove_gridlines(workbook['summary'])
    remove_gridlines(workbook['source_code'])
    remove_gridlines(workbook['commits'])
    remove_gridlines(workbook['tags'])

    # Make header text bold for all sheets except the summary sheet
    for sheet_name in ['source_code', 'commits', 'tags']:
        sheet = workbook[sheet_name]
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        adjust_column_width(sheet)
        align_cells(sheet)

    # Calculate run duration
    run_duration = datetime.now() - start_time
    hours, remainder = divmod(run_duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_run_duration = f"{int(hours)} hours, {int(minutes)} minutes, {seconds:.1f} seconds"

    # Write summary data
    summary_data = {
        'Report Title': f"Project {project_name} Git Report.",
        'Purpose of the report': f"This report provides a detailed view of the Git repositories in project {project_name}.",
        'Run Date': datetime.now().strftime('%d-%b-%Y %I:%M %p'),
        'Run Duration': formatted_run_duration,
        'Run By': getpass.getuser(),
        'Input': ', '.join([f"{col}: {row[col]}" for index, row in config_df.iterrows() for col in config_df.columns if col != 'PAT' and not pd.isna(row[col]) and row[col] != ''])
    }

    row = 1
    for key, value in summary_data.items():
        worksheet_summary.cell(row=row, column=1).value = key
        worksheet_summary.cell(row=row, column=1).fill = PatternFill(start_color='000080', end_color='000080', fill_type='solid')
        worksheet_summary.cell(row=row, column=1).font = Font(color='FFFFFF', bold=True)
        worksheet_summary.cell(row=row, column=2).value = value
        worksheet_summary.cell(row=row, column=2).alignment = Alignment(horizontal='left')
        row += 1

    for i in range(len(summary_data)):
        worksheet_summary.column_dimensions['A'].width = 26.71  # Adjust column A width
        worksheet_summary.column_dimensions['B'].width = 85.87  # Adjust column B width
        worksheet_summary.row_dimensions[i + 1].height = 30  # Adjust row height

    apply_black_border(worksheet_summary)  # Apply black border to summary sheet

    workbook.save(output_path)


def process(server_url, pat, project, repository_name, branch_name):
    api_version = '6.0'  # Change this if your server uses a different version

    # Print the server URL and project for debugging
    print(f"Server URL: {server_url}")
    print(f"Project: {project}")
    print(f"Repo: {repository_name}")
    print(f"Branch: {branch_name}")

    # Authenticate and get projects (optional step to confirm login)
    projects = authenticate_and_get_projects(server_url, pat, api_version)
    if projects:
        # Retrieve repository info
        repositories = get_repositories(server_url, project, pat, api_version)
        if repositories:
            for repo in repositories['value']:
                if repo['name'] == repository_name:
                    repo_id = repo['id']

                    data_source_code = []
                    data_commits = []
                    data_all_commits = []
                    data_tags = []

                    # Get branches
                    branches = get_branches(server_url, project, repo_id, pat, api_version)
                    if branches:
                        branch_names = [branch['name'].replace('refs/heads/', '') for branch in
                                        branches] if branch_name is None else [branch_name]
                        for branch in branch_names:
                            commit_id, comment, author, last_modified = get_latest_commit_info(server_url, project,
                                                                                               repo_id, branch, pat,
                                                                                               api_version)
                            if commit_id:
                                # Get all commits for the branch
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
                                        print(f"Processing file: {file}")  # Debugging statement
                                        is_folder = file.get('isFolder', file['gitObjectType'] == 'tree')
                                        if not is_folder:
                                            sha1 = file['objectId']
                                            size = get_file_size(server_url, project, repo_id, sha1, pat, api_version)
                                            try:
                                                commit_count = get_commit_count(server_url, project, repo_id,
                                                                                file['path'], pat, api_version)
                                            except Exception as e:
                                                print(f'Failed to retrieve commit count for {file["path"]}: {e}')
                                                commit_count = 0
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
                                            'Path': file['path'],  # Relative path from the repository root
                                            'Size (Bytes)': int(size),
                                            'Last Modified Time': last_modified,
                                            'Author': author,
                                            'Comments': comment,
                                            'Commit ID': commit_id,
                                            'Commit Count': commit_count
                                        }
                                        data_source_code.append(file_info)

                    # Get all commits in the repository
                    all_commits = get_all_repo_commits(server_url, project, repo_id, pat, api_version)
                    tags = get_tags(server_url, project, repo_id, pat, api_version)

                    for tag in tags:
                        tag_id = tag['objectId']
                        tag_details = get_tag_details(server_url, project, repo_id, tag_id, pat, api_version)
                        if tag_details:
                            commit_details = get_commit_details(server_url, project, repo_id,
                                                                tag_details['taggedObject']['objectId'], pat,
                                                                api_version)
                            if commit_details:
                                tag_date, tag_time = tag_details['taggedBy']['date'].split('T')
                                tag_time = tag_time.split('Z')[0]
                                tag_info = {
                                    'Tag Name': tag['name'].replace('refs/tags/', ''),
                                    'Tag ID': tag['objectId'],
                                    'Tag Message': tag_details['message'],
                                    'Commit ID': tag_details['taggedObject']['objectId'],
                                    'Commit Message': commit_details['comment'],
                                    'Author': tag_details['taggedBy']['name'],
                                    'Date & Time': f"{tag_date} {tag_time}"
                                }
                                data_tags.append(tag_info)

                    commit_tag_map = map_commit_tags(tags)
                    for commit in all_commits:
                        tag_name = commit_tag_map.get(commit['commitId'], 'not tagged')
                        all_commit_info = {
                            'Author': commit['author']['name'],
                            'Commit Message': commit['comment'],
                            'Commit ID': commit['commitId'],
                            'Commit Date': commit['author']['date'],
                            'Tag Name': tag_name  # Include the Tag Name column
                        }
                        data_all_commits.append(all_commit_info)

                    return data_source_code, data_commits, data_all_commits, data_tags
    return [], [], [], []


def construct_input(df):
    result = defaultdict(lambda: {"pat": "", "projects": []})

    for index, row in df.iterrows():
        if pd.isna(row['Server URL']) or pd.isna(row['PAT']):
            print(f"Skipping row {index + 1} due to missing data. ServerURL and PAT values are mandatory.")
            continue

        server_url = row['Server URL'].rstrip('/')
        pat = row['PAT']
        project_name = row.get('Project Name')
        repo_name = row.get('Repository Name')
        branch_name = row.get('Branch Name')

        # Update the PAT only if it's not already set for this server URL
        if not result[server_url]["pat"]:
            result[server_url]["pat"] = pat

        # Process row based on the presence of project name
        if project_name:
            # Check if the project already exists
            project = next((p for p in result[server_url]["projects"] if p["name"] == project_name), None)
            if not project:
                project = {"name": project_name, "repos": []}
                result[server_url]["projects"].append(project)
        else:
            # If project name is empty, retrieve all projects and their repos
            for proj_name in get_project_names(devops_server_url=server_url, pat=pat):
                # Check if the project already exists
                project = next((p for p in result[server_url]["projects"] if p["name"] == proj_name), None)
                if not project:
                    project = {"name": proj_name, "repos": []}
                    result[server_url]["projects"].append(project)

                # Fetch repos for each project when project_name is empty
                for repo_name in get_repo_names_by_project(devops_server_url=server_url, pat=pat, project_name=proj_name):
                    repo = next((r for r in project["repos"] if r["name"] == repo_name), None)
                    if not repo:
                        repo = {"name": repo_name, "branches": []}
                        project["repos"].append(repo)
            continue  # Skip further processing for this row since we already handled all projects and repos

        # Prepare repository structure if project_name is specified
        if repo_name:
            # Check if repo already exists under this project
            repo = next((r for r in project["repos"] if r["name"] == repo_name), None)
            if not repo:
                # If repo does not exist, create it with branches
                repo = {"name": repo_name, "branches": []}
                project["repos"].append(repo)

            # Add branch if specified and unique
            if branch_name and branch_name not in repo["branches"]:
                repo["branches"].append(branch_name)
        else:
            # If repo is not specified, retrieve repos for the project
            for repo_name in get_repo_names_by_project(devops_server_url=server_url, pat=pat, project_name=project_name):
                repo = next((r for r in project["repos"] if r["name"] == repo_name), None)
                if not repo:
                    repo = {"name": repo_name, "branches": []}
                    project["repos"].append(repo)

    # Convert default dict to normal dict for final output
    return dict(result)


def main():
    input_file = r'git_discovery_input_form.xlsx'
    run_id = str(int(datetime.now().strftime("%Y%m%d%H%M%S")))
    output_directory = os.path.join("Git", run_id)

    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    df = pd.read_excel(input_file)
    # Read the values from the Excel file and strip any leading/trailing spaces
    df['Server URL'] = df['Server URL'].fillna('').str.strip()
    df['Project Name'] = df['Project Name'].fillna('').str.strip()
    df['PAT'] = df['PAT'].fillna('').str.strip()
    df['Repository Name'] = df['Repository Name'].fillna('').str.strip()
    df['Branch Name'] = df['Branch Name'].fillna('').str.strip()

    # Form the input data in below format
    # Sample format below
    """
        {
           "server_url":{
              "pat":"123test_token",
              "projects":[
                 {
                    "name":"proj_name",
                    "repos":[
                       {
                          "name":"repo_name",
                          "branches":["branch_name_1", "branch_name_2"]
                       }
                    ]
                 }
              ]
           }
        }
    """
    input_data = construct_input(df)
    print(f"Final input combination: {input_data}")

    for server_url, server_data in input_data.items():
        pat = server_data["pat"]
        for project in server_data["projects"]:
            proj_name = project["name"]
            print(f"Processing project {proj_name}")
            master_data_source_code = []
            master_data_commits = []
            master_data_all_commits = []
            master_data_tags = []
            for repo in project["repos"]:
                repo_name = repo["name"]
                branches = repo.get("branches", [])
                # If branches exist, iterate through them; otherwise, use an empty string for branch_name
                for branch_name in branches if branches else [None]:
                    data_source_code, data_commits, data_all_commits, data_tags = process(server_url, pat, proj_name, repo_name, branch_name)
                    master_data_source_code = master_data_source_code + data_source_code
                    master_data_commits = master_data_commits + data_commits
                    master_data_all_commits = master_data_all_commits + data_all_commits
                    master_data_tags = master_data_tags + data_tags
            # Create the output file name with the desired format
            output_filename = f"{proj_name}_git_discovery_report.xlsx"
            output_path = os.path.join(output_directory, output_filename)
            generate_report(master_data_source_code, master_data_commits, master_data_all_commits, master_data_tags,
                            output_path, proj_name, df)
            print(f'Report generated: {output_path}')


if __name__ == "__main__":
    main()
