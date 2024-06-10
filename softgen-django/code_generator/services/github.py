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

    def delete_file(self, repository_name, file_path, commit_message, branch="main"):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                contents = repo.get_contents(file_path, ref=branch)
                response = repo.delete_file(contents.path, commit_message, contents.sha, branch=branch)
                print(f"File {file_path} successfully deleted from {branch} branch.")
                return response
            except GithubException as e:
                raise GithubException(f"Error deleting file {file_path} from repository {repository_name}: {str(e)}")
        else:
            raise Exception(f"Error deleting file {file_path} from repository {repository_name}: Repository not found.")

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

    def delete_repo_by_url(self, repo_url):
        try:
            user_repo = repo_url.split('/')[-1]
            repo = self.get_repository(user_repo)
            repo.delete()
            print(f"Repositório '{user_repo}' deletado com sucesso.")
        except GithubException as e:
            raise GithubException(f"Error deleting repository {repo_url}: {str(e)}")
        
    def create_branch(self, repository_name, branch, main_branch='main'):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                main_branch = repo.get_branch(main_branch)
                response = repo.create_git_ref(ref=f'refs/heads/{branch}', sha=main_branch.commit.sha)
                print(f"Branch {branch} successfully created in {repository_name} repository.")
                return response
            except GithubException as e:
                raise GithubException(f"Error creating branch {branch} on repository {repository_name}: {str(e)}")
        else:
            raise Exception(f"Error creating branch {branch} on repository {repository_name}: Repository not found.")
        
    def merge_branch(self, repository_name, source_branch, target_branch='main'):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                response = repo.merge(target_branch, source_branch, f'Merge branch {source_branch} into {target_branch}')
                print(f'Branch {source_branch} merged into {target_branch} successfully.')
                return response
            except GithubException as e:
                raise GithubException(f"Error merging branch {source_branch} into {target_branch} on repository {repository_name}: {str(e)}")
        else:
            raise Exception(f"Error merging branch {source_branch} into {target_branch} on repository {repository_name}: Repository not found.")

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

def update_software_files(software_id, version):
    software = Software.objects.get(pk=software_id)
    files = software.files.filter(version=version)
    
    if not files:
        raise ValueError(f"No files found with version {version} for software id {software_id}.")

    repo_url = software.github_repo_url
    if not repo_url:
        raise ValueError(f"No GitHub repository URL found for software id {software_id}.")
    
    repo_name = repo_url.split('/')[-1]
    branch = f'v{version}'

    # Creating a branch so Vercel deployment will only be triggered after all files have been uploaded
    git_manager.create_branch(repo_name, branch)
    
    for file in files:
        try:
            if not file.content:
                git_manager.delete_file(repo_name, file.path, file.instructions, branch)
            else:
                # Adds if does not exist
                git_manager.update_file(repo_name, file.path, file.instructions, file.content, branch)
        except GithubException as e:
            print(f"Error updating/deleting file {file.path} in repository {repo_name}: {str(e)}")

    git_manager.merge_branch(repo_name, branch, 'main')

    print(f'Software id {software_id} files with version {version} updated in GitHub repository {repo_name} successfully.')
