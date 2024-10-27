import os
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import credentials

# Read the Excel file
excel_file = 'collection_input_form.xlsx'
df = pd.read_excel(excel_file, sheet_name='Sheet1')

# Extract all DevOps server URLs from the Excel file, starting from the second row
urls = df['Server URL'].dropna().tolist()  # Drop any NaN values and convert to a list

# Remove any leading or trailing whitespace from URLs
urls = [url.strip() for url in urls]

# Access Tokens
pats = credentials.PAT

# Ensure the number of PATs matches the number of URLs
if len(pats) != len(urls):
    raise ValueError("The number of PATs does not match the number of server URLs. Please check your credentials.py file.")

# Specify the save location for the Excel files
save_directory = os.path.join(os.getcwd(), 'Collections')
os.makedirs(save_directory, exist_ok=True)  # Create the directory if it does not exist

for i, devops_server_url in enumerate(urls):
    pat = pats[i]  # Get the corresponding PAT for the current server URL
    # Extract the collection name from the URL
    collection_name = devops_server_url.split('/')[-1]
    print(f"Processing DevOps Server Collection: {collection_name}")

    # Create a DataFrame writer object to save multiple sheets
    save_path = os.path.join(save_directory, f'{collection_name}_discovery_report.xlsx')
    with pd.ExcelWriter(save_path, engine='xlsxwriter') as writer:
        
        # API endpoint to get the list of projects
        projects_api_url = f'{devops_server_url}/_apis/projects?api-version=6.0'
        
        # Making the request to the API
        response = requests.get(projects_api_url, auth=HTTPBasicAuth('', pat))
        
        if response.status_code == 200:
            try:
                projects = response.json()['value']
                for project in projects:
                    project_name = project['name']
                    print(f"Processing project: {project_name}")
                    
                    project_data = []

                    # Check for Git repositories
                    repos_api_url = f'{devops_server_url}/{project_name}/_apis/git/repositories?api-version=6.0'
                    repo_response = requests.get(repos_api_url, auth=HTTPBasicAuth('', pat))

                    if repo_response.status_code == 200:
                        try:
                            repos = repo_response.json()['value']
                            if repos:
                                for repo in repos:
                                    repo_name = repo['name']

                                    # Check for branches in each Git repository
                                    branches_api_url = f'{devops_server_url}/{project_name}/_apis/git/repositories/{repo_name}/refs?api-version=6.0&filter=heads/'
                                    branches_response = requests.get(branches_api_url, auth=HTTPBasicAuth('', pat))

                                    if branches_response.status_code == 200:
                                        try:
                                            branches = branches_response.json()['value']
                                            if branches:
                                                for branch in branches:
                                                    branch_name = branch['name'].replace('refs/heads/', '')
                                                    project_data.append([collection_name, project_name, repo_name, branch_name])
                                            # If there are no branches, do not add any entry
                                        except (ValueError, KeyError) as e:
                                            print(f"    Error parsing JSON response for branches in repository '{repo_name}':", e)
                                    else:
                                        print(f"    Failed to retrieve branches for repository '{repo_name}'. Status code: {branches_response.status_code}")
                        except (ValueError, KeyError) as e:
                            print(f"  Error parsing JSON response for Git repositories in project '{project_name}':", e)
                    else:
                        print(f"  Failed to retrieve Git repositories for project '{project_name}'. Status code: {repo_response.status_code}")
                    
                    # Check for TFVC branches
                    tfvc_check_api_url = f'{devops_server_url}/{project_name}/_apis/tfvc/branches?api-version=6.0'
                    tfvc_response = requests.get(tfvc_check_api_url, auth=HTTPBasicAuth('', pat))

                    if tfvc_response.status_code == 200:
                        try:
                            tfvc_branches = tfvc_response.json()['value']
                            print(f"TFVC branches for project '{project_name}': {tfvc_branches}")  # Debugging output
                            root_path = f"$/{project_name} [root]"
                            # Always include the root path
                            project_data.append([collection_name, project_name, 'TFVC', root_path])
                            if tfvc_branches:
                                for tfvc_branch in tfvc_branches:
                                    # Try to get the branch name from different possible fields
                                    branch_name = tfvc_branch.get('name') or tfvc_branch.get('path') or 'Unnamed Branch'
                                    project_data.append([collection_name, project_name, 'TFVC', branch_name])
                        except (ValueError, KeyError) as e:
                            print(f"  Error parsing JSON response for TFVC in project '{project_name}':", e)
                    else:
                        print(f"  Failed to retrieve TFVC branches for project '{project_name}'. Status code: {tfvc_response.status_code}")

                    # Convert project data to DataFrame and write to Excel sheet
                    if project_data:
                        project_df = pd.DataFrame(project_data, columns=['Collection', 'Project Name', 'Repository Name', 'Branch Name'])
                        project_df.to_excel(writer, sheet_name=project_name[:31], index=False)  # Excel sheet names can only be up to 31 characters long

            except (ValueError, KeyError) as e:
                print('Error parsing JSON response:', e)
        else:
            print(f'Failed to retrieve projects for URL {devops_server_url}. Status code: {response.status_code}')

    print(f"Report generated successfully: {save_path}")
