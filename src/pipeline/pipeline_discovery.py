



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
log_file = 'logs'

# Clear the log file before starting a new run
with open(log_file, 'w'):
    pass

logging.basicConfig(filename=log_file, 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_print(msg):
    logging.info(msg)
    print(msg)

def get_pipeline_details(project_):
    url = f"{instance}/{project_}/_apis/build/definitions?api-version=6.0"

    response = requests.get(url, auth=HTTPBasicAuth(username, pat))

    if response.status_code == 200:
        data = response.json()
        if data['count'] > 0:
            for pipeline in data['value']:
                pipeline_id = pipeline['id']
                log_print(f"Processing the pipeline Id {pipeline_id}")
                file_url = f"{instance}/{project_}/_apis/pipelines/{pipeline_id}?revision=1"
                response = requests.get(file_url, auth=HTTPBasicAuth(username, pat))
                data = response.json()
                # log_print(file_url)
                variable_groups ={}
                variables={}
                detailedJson = data['configuration'].get('designerJson')
                executionPolicy =[]
                agent_details = []
                artifact_details=''
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
                    url = f"{instance}/_apis/git/repositories/{repository_id}?api-version=6.1-preview"
                    response = requests.get(url, auth=HTTPBasicAuth('', pat))

                    if response.status_code == 200:
                        repo_data = response.json()
                        repo_name = repo_data["name"]
                        log_print(f"Repository Name: {repo_name}")
                    else:
                        log_print(f"Failed to fetch repository details: {response.status_code}")
                        log_print("Response content: " + response.text)

                path = data['configuration'].get('path', 'NA')
                if path == 'NA':
                    is_classic = 'Yes'
                else:
                    is_classic = 'No'

                collection = instance.split('/')

                url = f"{instance}/{project_}/_apis/build/definitions/{pipeline_id}?api-version=6.1-preview"
                response = requests.get(url , auth=HTTPBasicAuth(username, pat))
                if response.status_code == 200:
                    data = response.json()
                    
                    if is_classic == 'Yes':
                        agent_details = pipeline.get('queue', {}).get('name')
                        phases = data['process'].get('phases',{})
                        if phases != {}:
                            for phase in phases:
                                queue=phase['target'].get('queue',{})
                                executionPolicy = phase['target']['executionOptions']
                                agent_id=""
                                if queue != {}:
                                    agent_id =phase['target']['queue'].get('id',{})
                                if phase:
                                    maxConcurrency =''
                                    continueOnError =''
                                    execution_type = phase['target']['executionOptions'].get('type')
                                    if execution_type != '' :
                                        maxConcurrency =phase['target']['executionOptions'].get('maxConcurrency', '')
                                        continueOnError =phase['target']['executionOptions'].get('continueOnError', '')
                                    
                                    phases_.append(phase['name'])
                                    phases_string = ', '.join(phases_)
                    else:
                        queue= data.get('queue',{})
                        if queue != {}:
                            agent_details=pipeline.get('queue', {}).get('name')
                        response_text = fetch_pipeline_yaml(pipeline_id, project_)
                        result = False
                        is_script_available = pd.isna(response_text)
                        if is_script_available is False:
                            result =is_release_pipeline(response_text)
                        is_classic = 'No (Release)' if result else is_classic

                else:
                    log_print(f"Failed to fetch additional details: {response.status_code}")
                    log_print("Response content: " + response.text)
                

                url=f"{instance}/{project_}/_apis/build/builds?definitions={pipeline_id}&api-version=6.0"
                response = requests.get(url , auth=HTTPBasicAuth(username, pat))
                if response.status_code == 200:
                    data = response.json()
                    build_count = data['count']
                    build = next((b for b in data.get('value', []) if b['status'] != 'notStarted' and b['result'] == 'succeeded'), None)
                    if build:
                        build_id = build['id']
                        url = f"{instance}/{project_}/_apis/build/builds/{build_id}/artifacts?api-version=6.0"
                        response = requests.get(url, auth=HTTPBasicAuth(username, pat))
                        if response.status_code == 200:
                            artifacts_data = response.json()
                            artifact_details = next((artifact['name'] for artifact in artifacts_data.get('value','')), None)        

                pipeline_info = {
                    'Pipeline ID': pipeline['id'],
                    'Name': pipeline['name'],
                    'Last Updated Date': pipeline['createdDate'],
                    'FileName': path,
                    'Variables': variables_count,
                    'Varibale Groups':variable_groups_count,
                    'Repository_type': repository.get('type'),
                    'Repository': repo_name,
                    'Classic Pipeline': is_classic,
                    'Agents': agent_details,
                    'Phases':phases_string.replace("'",''),
                    'Execution Type':execution_type,
                    'Max Concurrency':maxConcurrency,
                    'ContinueOn Error': continueOnError,
                    'Builds': build_count,
                    'Artifacts':artifact_details
                }
                pipeline_data.append(pipeline_info)
            # df = pd.DataFrame(pipeline_data)
            # format_excel(df,"Builds")
        else:
            log_print(f"No pipeline found in this project - {project_}")
            return False
    else:
        log_print(f"Failed to retrieve data. Status Code: {response.status_code} - {response.text}")
    return True

def is_release_pipeline(response_text):
    deploy_keywords = ['DeployStaging', 'DeployProduction','resources','DownloadBuildArtifacts']
    for keyword in deploy_keywords:
        if keyword.lower() in response_text.lower():
            return True  
    return False


def fetch_pipeline_yaml(pipeline_id_discovery, project_):
    pipeline_id =pipeline_id_discovery
    pipeline_details_url = f"{instance}/{project_}/_apis/pipelines/{pipeline_id}?revision=1"
    pipeline_response = requests.get(pipeline_details_url,auth=HTTPBasicAuth(username, pat))
    if pipeline_response.status_code != 200:
        log_print(f"Error fetching pipeline details: {pipeline_response.status_code} - {pipeline_response.text}")
        return
    pipeline_data = pipeline_response.json()
    repo_id = pipeline_data["configuration"]["repository"]["id"]
    file_path = pipeline_data["configuration"]["path"]
    download_yaml_url = f"{instance}/{project_}/_apis/git/repositories/{repo_id}/items?path={file_path}&api-version=6.0"
    yaml_response = requests.get(
        download_yaml_url,
        auth=HTTPBasicAuth(username, pat)
    )
    if yaml_response.status_code != 200:
        log_print(f"Error downloading YAML file: {yaml_response.status_code} - {yaml_response.text}")
        return 
    return yaml_response.text

def get_releases( project ):
    url = f"{instance}/{project}/_apis/release/definitions?api-version=6.0"
    response = requests.get(url,auth=HTTPBasicAuth(username, pat))
    if response.status_code == 200:
        data = response.json()
        if data.get('count', 0) > 0:
            for release in data.get('value', []) :
                release_id =release['id']
                log_print(f"Processing the release Id {release_id}")
                url = f"{instance}/{project}/_apis/release/definitions/{release_id}?api-version=6.1-preview"
                response = requests.get(url, auth=HTTPBasicAuth('', pat))
                if response.status_code == 200:
                    release_pipeline = response.json()
                    variables = release_pipeline.get('variables')
                    variable_groups = release_pipeline.get('variableGroups')
                    artifacts_count = len(release_pipeline.get('artifacts'))
                    variable_groups_count = len(variable_groups)
                    variables_count = len(variables)
                    
                    environment_details = []                   
                    for environment in release_pipeline['environments']:
                        concurrencyCount = environment['executionPolicy'].get('concurrencyCount',"")
                        queueDepthCount = environment['executionPolicy'].get('queueDepthCount',"")                   
                        # if 'deployPhases' in environment:
                        for deploy_phase in environment.get('deployPhases',{}):                               
                            if 'deploymentInput' in deploy_phase:
                                maxNumberOfAgents =''
                                continueOnError =''
                                parallel_execution_type = deploy_phase['deploymentInput']['parallelExecution'].get('parallelExecutionType', '')
                                if parallel_execution_type != 'none':
                                    maxNumberOfAgents =deploy_phase['deploymentInput']['parallelExecution'].get('maxNumberOfAgents', '')
                                    continueOnError =deploy_phase['deploymentInput']['parallelExecution'].get('continueOnError', '')

                                queue_id = deploy_phase['deploymentInput'].get('queueId',{})
                                agent_pool_details = get_agent_pool_details(project, queue_id)
                                if agent_pool_details:
                                    environment_details=agent_pool_details.get('name')
                else:
                    log_print(f"Failed to fetch variables - {response.status_code}-{response.text}")

                collection = instance.split('/')

                releases_info = {
                    'Release ID': release['id'], 
                    'Name': release['name'],       
                    'Created Date': release['createdOn'], 
                    'Last Updated Date': release['modifiedOn'],  
                    'Variable': variables_count,
                    'Variable Groups': variable_groups_count,
                    'Artifacts': artifacts_count,
                    'Agents':environment_details,
                    'Parallel Execution Type': parallel_execution_type,
                    'Max Agents': maxNumberOfAgents,
                    'ContinueOnError':continueOnError,
                    'Concurrency Count':concurrencyCount,
                    'QueueDepth Count':queueDepthCount
                }
                releases_data.append(releases_info)
        else:
            log_print(f"No release found in the project - {project}")  
    else:
        log_print(f"Failed to fetch releases. Status Code: {response.status_code} - {response.text}")
    
def get_agent_pool_details(project, queue_id):
    url=f"{instance}/{project}/_apis/distributedtask/queues/{queue_id}?api-version=6.0-preview"
    response = requests.get(url, auth=HTTPBasicAuth(username, pat))
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return False

def format_excel(df, type):
    folder_path="output_folder"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")   # Format as "HH-MM-SS"

    if type == "Builds":
        excel_name = os.path.join(folder_path, f"discovery_build_{id}.xlsx")
    else:
        excel_name = os.path.join(folder_path, f"discovery_release_{id}.xlsx")
    with pd.ExcelWriter(excel_name, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=type)
        worksheet = writer.sheets[type]
        for col_num, column in enumerate(df.columns):
            # Find the maximum length of the column content
            max_length = max(df[column].astype(str).apply(len).max(), len(column)) + 2  
            worksheet.set_column(col_num, col_num, max_length)

        # artifact_column_idx = df.columns.get_loc('Agents/Stages')
        # parallel_column_idx = df.columns.get_loc('Parallel Execution')
        # worksheet.set_column(artifact_column_idx, artifact_column_idx, 80, None, {'text_wrap': True})
        # worksheet.set_column(parallel_column_idx, parallel_column_idx, 50, None, {'text_wrap': True})

if __name__ == "__main__":
    config_df = pd.read_excel('input_discovery.xlsx')
    pipeline_data = []
    instance = config_df.loc[0, 'Instance']
    project_name = config_df.loc[0, 'Project']
    username = config_df.loc[0, 'Username']
    pat = config_df.loc[0, 'Pat']
    releases_data=[]
    # if pd.isna(project_name):
    #     url = f"{instance}/_apis/projects?api-version=6.0"
    #     response = requests.get(url, auth=HTTPBasicAuth(username, pat))
    #     if response.status_code == 200:
    #         projects = response.json()
    #         log_print("List of projects:")
    #         for project in projects['value']:
    #             log_print(f"Project Name: {project['name']}, Project ID: {project['id']}")
    #             temp = get_pipeline_details(project['name'])
    #             get_releases(project['name'])
    #     else:
    #         log_print(f"Failed to retrieve projects. Status Code: {response.status_code}-{response.text}")
    #     log_print("Pipeline information has been exported to excel")
    # else:
    result = get_pipeline_details(project_name)
    if pipeline_data:
        df = pd.DataFrame(pipeline_data)
        format_excel(df,"Builds")
        log_print("Build information has been exported to excel")
    get_releases(project_name)
    if releases_data:
        df = pd.DataFrame(releases_data)
        format_excel(df,"Release")  
        log_print("Release information has been exported to excel")
