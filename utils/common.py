import requests
from requests.auth import HTTPBasicAuth


def get_project_names(devops_server_url, pat):
    project_names = []

    projects_api_url = f'{devops_server_url}/_apis/projects?api-version=6.0'
    response = requests.get(projects_api_url, auth=HTTPBasicAuth('', pat))

    if response.status_code == 200:
        try:
            projects = response.json()['value']
            for project in projects:
                project_name = project['name']
                project_names.append(project_name)
        except (ValueError, KeyError) as e:
            print('Error parsing JSON response for retrieving collections projects:', e)
    else:
        print(f'Failed to retrieve projects for URL {devops_server_url}. Status code: {response.status_code}')

    return project_names


def get_repo_names_by_project(devops_server_url, pat, project_name):
    repo_names = []

    repos_api_url = f'{devops_server_url}/{project_name}/_apis/git/repositories?api-version=6.0'
    repo_response = requests.get(repos_api_url, auth=HTTPBasicAuth('', pat))

    if repo_response.status_code == 200:
        try:
            repos = repo_response.json()['value']
            if repos:
                for repo in repos:
                    repo_name = repo['name']
                    repo_names.append(repo_name)
        except (ValueError, KeyError) as e:
            print(f"Error parsing JSON response for Git repositories in project '{project_name}':", e)
    else:
        print(f"Failed to retrieve Git repositories for project '{project_name}'. "
              f"Status code: {repo_response.status_code}. URL: {devops_server_url}")

    return repo_names


def add_project_if_not_exists(lst, values):
    for value in values:
        if value.lower() not in map(str.lower, lst):
            lst.append(value)


if __name__ == "__main__":
    url = "http://172.191.4.85/TestCollection"
    ptoken = ""
    pro_names = get_project_names(url, ptoken)
    print(pro_names)
    pro_name = "devserver"
    rep_names = get_repo_names_by_project(url, ptoken, pro_name)
    print(rep_names)
