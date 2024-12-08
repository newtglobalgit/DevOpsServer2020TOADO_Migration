import base64
import datetime
import logging
import os
import requests
import json
import openpyxl
import pandas as pd
from requests.auth import HTTPBasicAuth

# Setup logging
log_file = 'logs_release'

# Clear the log file before starting a new run
with open(log_file, 'w'):
    pass

logging.basicConfig(filename=log_file, 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_print(msg):
    logging.info(msg)
    print(msg)

def get_releases( project ):

    # Construct the API URL for releases
    url = f"{instance}/{project}/_apis/release/definitions?api-version=6.0"

    # Make the API request
    response = requests.get(url,auth=HTTPBasicAuth(username, pat))

    if response.status_code == 200:
        # Parse the response
        data = response.json()
        if data['count'] > 0:
            for release in data['value']:  # Iterate through the list of releases
                release_id =release['id']
                url = f"{instance}/{project}/_apis/release/definitions/{release_id}?api-version=6.1-preview"
                response = requests.get(url, auth=HTTPBasicAuth('', pat))
                if response.status_code == 200:
                    release_pipeline = response.json()
                    variables = release_pipeline.get('variables')
                    variable_groups = release_pipeline.get('variableGroups')
                    artifacts_count = len(release_pipeline.get('artifacts'))
                    # if variable_groups:
                        # variable_groups_name= check_variable_group_exists(variable_groups, project)
                    variable_groups_count = len(variable_groups)
                    variables_count = len(variables)
                    
                    # Initialize lists to store environment details
                    environment_details = []
                    
                    # Loop through all environments
                    for environment in release_pipeline['environments']:
                        env_name = environment.get('name', 'Unknown')
                        executionPolicy = environment.get('executionPolicy', {})                       
                        if 'deployPhases' in environment:
                            for deploy_phase in environment['deployPhases']:                               
                                if 'deploymentInput' in deploy_phase:
                                    parallel_execution = deploy_phase['deploymentInput'].get('parallelExecution', {})
                                    queue_id = deploy_phase['deploymentInput'].get('queueId',{})
                                    agent_pool_details = get_agent_pool_details(project, queue_id)
                                    if agent_pool_details:
                                        environment_details.append({
                                            'environment': env_name,
                                            'agent_pool': agent_pool_details.get('name'),
                                            'agent_pool_id': agent_pool_details.get('id')
                                        })
                    
                else:
                    log_print(f"Failed to fetch variables - {response.status_code}")
                    log_print(f"Response Content - {response.text}")
                collection = instance.split('/')

                releases_info = {
                    'Collection': collection[-1],
                    'Project': project,
                    'Release ID': release['id'], 
                    'Name': release['name'],       
                    'Created Date': release['createdOn'], 
                    'Last Updated Date': release['modifiedOn'],  
                    'Variable': variables_count,
                    'Variable Groups': variable_groups_count,
                    'Artifacts': artifacts_count,
                    'Agents/Stages':environment_details,
                    'Parallel Execution': parallel_execution,
                    'Execution Policy': executionPolicy
                }
                releases_data.append(releases_info)
        else:
            log_print(f"No release found in the project - {project}")
           
    else:
        log_print(f"Failed to fetch releases. Status Code: {response.status_code}")
        log_print("Response content:", response.text)

def format_excel(df):
    folder_path="output_folder"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")   # Format as "HH-MM-SS"
    excel_name = os.path.join(folder_path, f"discovery_release_{id}.xlsx")
    with pd.ExcelWriter(excel_name, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Releases")

        worksheet = writer.sheets["Releases"]
        
        for col_num, column in enumerate(df.columns):
            # Find the maximum length of the column content
            max_length = max(df[column].astype(str).apply(len).max(), len(column)) + 2  
            worksheet.set_column(col_num, col_num, max_length)
        # Specifically set a wide column width for 'Artifacts' column
        artifact_column_idx = df.columns.get_loc('Agents/Stages')
        parallel_column_idx = df.columns.get_loc('Parallel Execution')
        worksheet.set_column(artifact_column_idx, artifact_column_idx, 80, None, {'text_wrap': True})
        worksheet.set_column(parallel_column_idx, parallel_column_idx, 50, None, {'text_wrap': True})

# Check if variable group exists by ID
def check_variable_group_exists(variable_groups_id, project):
    variable_group_names =[]
    for variable_group_id in variable_groups_id:
        url = f"{instance}/{project}/_apis/distributedtask/variablegroups/{variable_group_id}?api-version=6.0-preview"
        response = requests.get(url, auth=HTTPBasicAuth(username, pat))
        
        if response.status_code == 200:
            data = response.json()
            variable_group_names.append(data['name'])  # Variable group exists
        elif response.status_code == 404:
            print("Variable group not found.")
            return False  # Variable group does not exist
        else:
            print(f"Failed to fetch variable group. Status Code: {response.status_code}")
            print(f"Response content: {response.text}")
            return False
        return variable_group_names
    
def get_agent_pool_details(project, queue_id):
    url=f"{instance}/{project}/_apis/distributedtask/queues/{queue_id}?api-version=6.0-preview"
    response = requests.get(url, auth=HTTPBasicAuth(username, pat))
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return False


# Main execution
if __name__ == "__main__":
    config_df = pd.read_excel('input_discovery.xlsx')

    instance = config_df.loc[0, 'Instance']
    project = config_df.loc[0, 'Project']
    username = config_df.loc[0, 'Username']
    pat = config_df.loc[0, 'Pat']
    
    releases_data=[]
    if pd.isna(project):
        # Construct URL to list all projects
        url = f"{instance}/_apis/projects?api-version=6.0"
        response = requests.get(url, auth=HTTPBasicAuth(username, pat))

        if response.status_code == 200:
            projects = response.json()
            log_print("List of projects:")
            for project in projects['value']:
                log_print(f"Project Name: {project['name']}, Project ID: {project['id']}")
                get_releases(project['name'])
                

        else:
            log_print(f"Failed to retrieve projects. Status Code: {response.status_code}")
            log_print("Response content:", response.text)
    
    else:
        get_releases(project)
        

    if releases_data:
        df = pd.DataFrame(releases_data)
        format_excel(df)  # Pass the dataframe to your format_excel function
        log_print("Discovery of release excel generated discovery_release.xlsx")