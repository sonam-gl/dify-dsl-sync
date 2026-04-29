import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DIFY_HOST: str          = os.getenv('DIFY_HOST', 'https://cloud.dify.ai')
    DIFY_ACCESS_TOKEN: str  = os.getenv('DIFY_ACCESS_TOKEN', '')
    DIFY_APP_ID: str        = os.getenv('DIFY_APP_ID', '')
    DIFY_APP_NAME: str      = os.getenv('DIFY_APP_NAME', 'app')
    GITHUB_TOKEN: str       = os.getenv('GITHUB_TOKEN', '')
    GITHUB_OWNER: str       = os.getenv('GITHUB_OWNER', '')
    GITHUB_REPO: str        = os.getenv('GITHUB_REPO', '')
    GITHUB_BRANCH: str      = os.getenv('GITHUB_BRANCH', 'main')
    GITHUB_FILE_PATH: str   = os.getenv('GITHUB_FILE_PATH', 'dsl/app.yml')

    def validate(self) -> None:
        required = [
            'DIFY_HOST', 'DIFY_ACCESS_TOKEN', 'DIFY_APP_ID',
            'GITHUB_TOKEN', 'GITHUB_OWNER', 'GITHUB_REPO',
        ]
        missing = [k for k in required if not getattr(self, k)]
        if missing:
            raise ValueError(f'Missing required env vars: {missing}')


config = Config()
config.validate()