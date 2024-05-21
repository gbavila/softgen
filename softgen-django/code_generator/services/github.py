from github import Github, GithubException
from django.conf import settings
from ..models import Software

class GitHubManager:
    def __init__(self):
        self.github = Github(settings.GITHUB_TOKEN)
        self.repo_prefix = self.github.get_user().login + '/'

    def get_repository(self, repository_name):
        repository_name = self.repo_prefix + repository_name
        try:
            return self.github.get_repo(repository_name)
        except GithubException as e:
            raise GithubException(f"Error accessing repository {repository_name}: {str(e)}")
        
    def create_repository(self, name, description="", private=True):
        try:
            user = self.github.get_user()
            repo = user.create_repo(name, description=description, private=private)
            print(f"Repositório '{name}' criado com sucesso.")
            return repo
        except GithubException as e:
            raise GithubException(f"Error creating repository {name}: {str(e)}")

    def create_file(self, repository_name, file_path, commit_message, content, branch="main"):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                response = repo.create_file(file_path, commit_message, content, branch=branch)
                print(f"File {file_path} successfully created in {branch} branch.")
                return response
            except GithubException as e:
                raise GithubException(f"Error creating file {file_path} on repository {repository_name}: {str(e)}")
        else:
            raise Exception(f"Error creating file {file_path} on repository {repository_name}: Repository not found.")

    def update_file(self, repository_name, file_path, commit_message, content, branch="main"):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                contents = repo.get_contents(file_path, ref=branch)
                response = repo.update_file(contents.path, commit_message, content, contents.sha, branch=branch)
                print(f"File {file_path} successfully updated to the {branch} branch.")
                return response
            except GithubException as e:
                raise GithubException(f"Error updating file {file_path} on repository {repository_name}: {str(e)}")
        else:
            raise Exception(f"Error updating file {file_path} on repository {repository_name}: Repository not found.")

    def get_commits(self, repository_name, branch="main"):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                commits = repo.get_commits(sha=branch)
                print("Commits:")
                for commit in commits:
                    print(commit.commit.message)
                return commits
            except GithubException as e:
                raise GithubException(f"Error listing commits on repository {repository_name}: {str(e)}")
        else:
            raise Exception(f"Error listing commits on repository {repository_name}: Repository not found.")

git_manager = GitHubManager()

def upload_software_to_github(repository, software_id):
    software = Software.objects.get(pk=software_id)
    files = software.files.all()
    repo = git_manager.create_repository(repository, f"{software.name} (id={software_id}): automatically generated software (Softgen)", private=True)

    for file in files:
        git_manager.create_file(repository, file.path, file.instructions, file.content)
    
    print(f'{software.name} (id={software_id}) code uploaded to github ({repository}) successfully.')    
    software.github_repo_url = repo.html_url
    software.save()
