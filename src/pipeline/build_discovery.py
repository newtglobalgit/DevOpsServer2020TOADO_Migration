import datetime
import os
import logging
from numpy import nan
import requests
import pandas as pd
from requests.auth import HTTPBasicAuth

# Setup logging
log_file = 'logs_pipeline'

# Clear the log file before starting a new run
with open(log_file, 'w'):
    pass

logging.basicConfig(filename=log_file, 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_print(msg):
    logging.info(msg)
    print(msg)

def format_excel(df):
    folder_path="output_folder"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")   # Format as "HH-MM-SS"
    excel_name = os.path.join(folder_path, f"discovery_pipeline_{id}.xlsx")

    with pd.ExcelWriter(excel_name, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Pipelines")
        # df_variables.to_excel(writer, index=False , sheet_name= 'Variable')
        
        worksheet = writer.sheets["Pipelines"]

        for col_num, column in enumerate(df.columns):
            # Find the maximum length of the column content
            max_length = max(df[column].astype(str).apply(len).max(), len(column)) + 2  
            worksheet.set_column(col_num, col_num, max_length)  

        # Set text wrapping for the 'Variables' column (last column)
        worksheet.set_column(df.columns.get_loc('Artifacts'), df.columns.get_loc('Artifacts'), 150, None, {'text_wrap': True})

def get_pipeline_details(project_):
    pipeline_info=""
    url = f"{instance}/{project_}/_apis/build/definitions?api-version=6.0"

    response = requests.get(url, auth=HTTPBasicAuth(username, pat))

    if response.status_code == 200:
        data = response.json()
        if data['count'] > 0:
            for pipeline in data['value']:
                pipeline_id = pipeline['id']
                
                log_print(f"Processing the pipelien Id {pipeline_id}")
                file_url = f"{instance}/{project_}/_apis/pipelines/{pipeline_id}?revision=1"
                
                response = requests.get(file_url, auth=HTTPBasicAuth(username, pat))
                data = response.json()
                log_print(file_url)
                variable_groups ={}
                variables={}
                detailedJson = data['configuration'].get('designerJson')
                executionPolicy =[]
                agent_details = []
                artifact_details=[]
                phases_=[]
                if detailedJson:
                    
                    variables = data['configuration']['designerJson'].get('variables', {})
                    variables_count= len(variables)
                    variable_groups = data['configuration']['designerJson'].get('variableGroups',{})
                    variable_groups_count= len(variable_groups)
                    repository = data['configuration']['designerJson'].get('repository', {})
                    repo_name = repository.get('name')
                    
                else:
                    variables = data['configuration'].get('variables', {})
                    variables_count= len(variables)
                    variable_groups = data['configuration'].get('variableGroups',{})
                    variable_groups_count= len(variable_groups)
                    repository = data['configuration'].get('repository', {})
                    repository_id = repository.get('id', "")
                    # Construct the API URL
                    url = f"{instance}/_apis/git/repositories/{repository_id}?api-version=6.1-preview"

                    # Send the GET request
                    response = requests.get(url, auth=HTTPBasicAuth('', pat))

                    if response.status_code == 200:
                        repo_data = response.json()
                        repo_name = repo_data["name"]
                        log_print(f"Repository Name: {repo_name}")
                    else:
                        log_print(f"Failed to fetch repository details: {response.status_code}")
                        log_print("Response content: " + response.text)

                path = data['configuration'].get('path', 'No path found')
                if path == 'No path found':
                    is_classic = 'Yes'
                else:
                    is_classic = 'No'

                collection = instance.split('/')

                url = f"{instance}/{project_}/_apis/build/definitions/{pipeline_id}?api-version=6.1-preview"
                response = requests.get(url , auth=HTTPBasicAuth(username, pat))
                if response.status_code == 200:
                    data = response.json()
                    
                    if is_classic == 'Yes':
                        agent_details.append({
                                                'agent_pool': pipeline.get('queue', {}).get('name'),
                                                'agent_pool_id': pipeline.get('queue', {}).get('id')
                                                })
                        phases = data['process'].get('phases',{})
                        for phase in phases:
                            queue=phase['target'].get('queue',{})
                            agent_id=""
                            if queue != {}:
                                agent_id =phase['target']['queue'].get('id',{})
                            executionPolicy.append({
                            'Phase Name': phase['name'],
                            'Execution Policy': phase['target'].get('executionOptions', {}),
                            'Agent Id':agent_id
                            })
                            phases_.append(phase['name'])
                    else:
                        queue= data.get('queue',{})
                        if queue != {}:
                            agent_details.append({
                                'agent_pool': pipeline.get('queue', {}).get('name'),
                                'agent_pool_id': pipeline.get('queue', {}).get('id')
                            })
                        response_text = fetch_pipeline_yaml(pipeline_id, project_)
                        result = False
                        is_script_available = pd.isna(response_text)
                        if is_script_available is False:
                            result =is_release_pipeline(response_text)
                        if result == True:
                            is_classic ='No (Release)'
                else:
                    log_print(f"Failed to fetch additional details: {response.status_code}")
                    log_print("Response content: " + response.text)
                

                url=f"{instance}/{project_}/_apis/build/builds?definitions={pipeline_id}&api-version=6.0"
                response = requests.get(url , auth=HTTPBasicAuth(username, pat))
                if response.status_code==200:
                    data = response.json()
                    build_count = data['count']
                    if build_count>0:
                        builds = data['value']
                        for build in builds:
                            if build['status']!='notStarted':
                                build_result = build['result']
                                if build_result == 'succeeded':
                                    build_id = build['id']
                                    url =f"{instance}/{project_}/_apis/build/builds/{build_id}/artifacts?api-version=6.0"
                                    response = requests.get(url , auth=HTTPBasicAuth(username, pat))
                                    if response.status_code == 200:
                                        data= response.json()
                                        if data['count'] > 0:
                                            artifacts= data['value']
                                            for artifact in artifacts:
                                                artifact_details = artifact
                                                break

                pipeline_info = {
                    'Collection': collection[-1],
                    'Project':project_,
                    'Pipeline ID': pipeline['id'],
                    'Name': pipeline['name'],
                    'Path': pipeline['path'],
                    'Last Updated Date': pipeline['createdDate'],
                    'FileName': path,
                    'Variables': variables_count,
                    'Varibale_Groups':variable_groups_count,
                    'Repository_type': repository.get('type'),
                    'Repository': repo_name,
                    'Classic Pipeline': is_classic,
                    'Agents': agent_details,
                    'ExecutionPolicy':executionPolicy,
                    'Phases':phases_,
                    'Builds': build_count,
                    'Artifacts':artifact_details


                }
                
                pipeline_data.append(pipeline_info)
            df = pd.DataFrame(pipeline_data)
            # df_variables = pd.DataFrame(pipeline_variables)
            format_excel(df)
        else:
            log_print(f"No pipeline found in this project - {project_}")
            return False
            
    else:
        log_print(f"Failed to retrieve data. Status Code: {response.status_code}")
        log_print("Response content: " + response.text)
    return True

def is_release_pipeline(response_text):
    # Check if the YAML content contains deployment-related keywords
    deploy_keywords = ['DeployStaging', 'DeployProduction','resources','DownloadBuildArtifacts']
    for keyword in deploy_keywords:
        if keyword.lower() in response_text.lower():
            return True  
    return False


# Fetch Pipeline YAML from the source
def fetch_pipeline_yaml(pipeline_id_discovery, project_):
    
    pipeline_id =pipeline_id_discovery
    pipeline_details_url = f"{instance}/{project_}/_apis/pipelines/{pipeline_id}?revision=1"
    pipeline_response = requests.get(
        pipeline_details_url,
        auth=HTTPBasicAuth(username, pat)
    )

    if pipeline_response.status_code != 200:
        print(f"Error fetching pipeline details: {pipeline_response.status_code} - {pipeline_response.text}")
        return

    pipeline_data = pipeline_response.json()
    # print(pipeline_data)
    repo_id = pipeline_data["configuration"]["repository"]["id"]
    file_path = pipeline_data["configuration"]["path"]

    # Endpoint to download YAML file
    download_yaml_url = f"{instance}/{project_}/_apis/git/repositories/{repo_id}/items?path={file_path}&api-version=6.0"

    yaml_response = requests.get(
        download_yaml_url,
        auth=HTTPBasicAuth(username, pat)
    )

    if yaml_response.status_code != 200:
        print(f"Error downloading YAML file: {yaml_response.status_code} - {yaml_response.text}")
        return 
    
    return yaml_response.text

if __name__ == "__main__":
    config_df = pd.read_excel('input_discovery.xlsx')
    pipeline_data = []

    instance = config_df.loc[0, 'Instance']
    project_name = config_df.loc[0, 'Project']
    username = config_df.loc[0, 'Username']
    pat = config_df.loc[0, 'Pat']
    
    if pd.isna(project_name):
        url = f"{instance}/_apis/projects?api-version=6.0"
        response = requests.get(url, auth=HTTPBasicAuth(username, pat))

        # Check response status and handle it
        if response.status_code == 200:
            projects = response.json()
            print("List of projects:")
            for project in projects['value']:
                print(f"Project Name: {project['name']}, Project ID: {project['id']}")
                temp = get_pipeline_details(project['name'])
        else:
            print(f"Failed to retrieve projects. Status Code: {response.status_code}")
            print("Response content:", response.text)
        log_print("Pipeline information has been exported to excel")

    else:
        result = get_pipeline_details(project_name)
        if result is True:
            log_print("Pipeline information has been exported to excel")
