import requests
import json
from django.conf import settings

class VercelManager:
    possible_status = ['BUILDING', 'ERROR', 'INITIALIZING', 'QUEUED', 'READY', 'CANCELED']
    frameworks = ["blitzjs", "nextjs", "gatsby", "remix", "astro", "hexo", "eleventy", "docusaurus-2", "docusaurus", "preact", "solidstart-1", "solidstart", "dojo", "ember", "vue", "scully", "ionic-angular", "angular", "polymer", "svelte", "sveltekit", "sveltekit-1", "ionic-react", "create-react-app", "gridsome", "umijs", "sapper", "saber", "stencil", "nuxtjs", "redwoodjs", "hugo", "jekyll", "brunch", "middleman", "zola", "hydrogen", "vite", "vitepress", "vuepress", "parcel", "sanity", "storybook"]
    
    def __init__(self):
        self.token = settings.VERCEL_TOKEN
        self.api_url = 'https://api.vercel.com'
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def handle_response(self, response):
        if response.status_code in range(200, 300):
            return response.json()
        else:
            try:
                error_message = response.json().get('error', {}).get('message', 'Unknown error')
            except json.JSONDecodeError:
                error_message = response.text
            raise Exception(f'Error {response.status_code}: {error_message}')
    
    def filter_target_deployments(self, json_response: list[dict], target: str):
        return [deployment for deployment in json_response if json_response.get('target') == target]

    def create_project(self, name, github_repo):
        url = f'{self.api_url}/v10/projects'
        data = {'name': name,
                'gitRepository': {
                    'repo': github_repo,
                    'type': 'github'
                }}
        response = requests.post(url, headers=self.headers, json=data)
        return self.handle_response(response)
    
    def create_deployment(self, project_id, repoId, branch='main', target=None):
        url = f'{self.api_url}/v13/deployments'
        data = {
            'name': project_id,
            'gitSource': {
                'type': 'github',
                'repoId': repoId,
                'ref': branch,
            },
            'target': target
        }
        response = requests.post(url, headers=self.headers, json=data)
        return self.handle_response(response)

    def list_deployments(self, project_id, target=None):
        url = f'{self.api_url}/v6/deployments'
        params = {'projectId': project_id}
        response = requests.get(url, headers=self.headers, params=params)
        return self.filter_target_deployments(self.handle_response(response), target)

    def get_deployment_by_id(self, deployment_id):
        url = f'{self.api_url}/v13/deployments/{deployment_id}'
        response = requests.get(url, headers=self.headers)
        return self.handle_response(response)

    def check_deployment_status(self, deployment_id):
        deployment = self.get_deployment_by_id(deployment_id)
        state = deployment.get('status')
        return {'id': deployment_id, 'status': state}

    def get_deployment_errors(self, deployment_id):
        url = f'{self.api_url}/v2/deployments/{deployment_id}/events'
        response = requests.get(url, headers=self.headers)
        events = self.handle_response(response)
        error_events = [event['payload']['text'] for event in events if 'error' in event['payload']['text'].lower()]
        return error_events
    
    def delete_project(self, project_id):
        url = f'{self.api_url}/v9/projects/{project_id}'
        response = requests.delete(url, headers=self.headers)
        return self.handle_response(response)
    
    def get_deployment_logs(self, deployment_id):
        url = f'{self.api_url}/v2/deployments/{deployment_id}/events'
        response = requests.get(url, headers=self.headers)
        return self.handle_response(response)
    
    def add_env_variable(self, project_id, key, value, target='production'):
        url = f'{self.api_url}/v10/projects/{project_id}/env'
        data = {
            'key': key,
            'value': value,
            'target': [target]
        }
        response = requests.post(url, headers=self.headers, json=data)
        return self.handle_response(response)

    def update_env_variable(self, project_id, env_id, key, value, target='production'):
        url = f'{self.api_url}/v9/projects/{project_id}/env/{env_id}'
        data = {
            'key': key,
            'value': value,
            'target': [target]
        }
        response = requests.patch(url, headers=self.headers, json=data)
        return self.handle_response(response)
    
    def delete_env_variable(self, project_id, env_id):
        url = f'{self.api_url}/v8/projects/{project_id}/env/{env_id}'
        response = requests.delete(url, headers=self.headers)
        return self.handle_response(response)

vercel_manager = VercelManager()
