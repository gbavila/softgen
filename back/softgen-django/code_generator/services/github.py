from github import Github, GithubException
from django.conf import settings

class GitHubManager:
    def __init__(self):
        self.github = Github(settings.GITHUB_TOKEN)
        self.repo_prefix = self.github.get_user().login + '/'

    def get_repository(self, repository_name):
        repository_name = self.repo_prefix + repository_name
        try:
            return self.github.get_repo(repository_name)
        except GithubException as e:
            raise GithubException(f"Erro ao acessar o repositório {repository_name}: {str(e)}")
        
    def create_repository(self, name, description="", private=True):
        try:
            user = self.github.get_user()
            repo = user.create_repo(name, description=description, private=private)
            print(f"Repositório '{name}' criado com sucesso.")
            return repo
        except GithubException as e:
            raise GithubException(f"Erro ao criar o repositório {name}: {str(e)}")

    def create_file(self, repository_name, file_path, commit_message, content, branch="main"):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                response = repo.create_file(file_path, commit_message, content, branch=branch)
                print(f"Arquivo {file_path} criado com sucesso no branch {branch}.")
                return response
            except GithubException as e:
                raise GithubException(f"Erro ao criar arquivo {file_path} no repositório {repository_name}: {str(e)}")
        else:
            raise Exception(f"Erro ao criar arquivo {file_path} no repositório {repository_name}: repositório não encontrado.")

    def update_file(self, repository_name, file_path, commit_message, content, branch="main"):
        repo = self.get_repository(repository_name)
        if repo:
            try:
                contents = repo.get_contents(file_path, ref=branch)
                response = repo.update_file(contents.path, commit_message, content, contents.sha, branch=branch)
                print(f"Arquivo {file_path} atualizado com sucesso no branch {branch}.")
                return response
            except GithubException as e:
                raise GithubException(f"Erro ao atualizar arquivo {file_path} no repositório {repository_name}: {str(e)}")
        else:
            raise Exception(f"Erro ao atualizar arquivo {file_path} no repositório {repository_name}: repositório não encontrado.")

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
                raise GithubException(f"Erro ao listar commits no repositório {repository_name}: {str(e)}")
        else:
            raise Exception(f"Erro ao listar commits no repositório {repository_name}: repositório não encontrado.")

git_manager = GitHubManager()
