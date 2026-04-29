import base64
import httpx
from typing import Optional, Tuple
from config import config


class GitHubClient:

    def __init__(self) -> None:
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Authorization': f'Bearer {config.GITHUB_TOKEN}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

    def _file_url(self, file_path: str) -> str:
        return (
            f'{self.base_url}/repos/'
            f'{config.GITHUB_OWNER}/{config.GITHUB_REPO}/contents/{file_path}'
        )

    async def get_file(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self._file_url(file_path),
                headers=self.headers,
                params={'ref': config.GITHUB_BRANCH},
            )
        if response.status_code == 404:
            return None, None
        response.raise_for_status()
        data = response.json()
        decoded = base64.b64decode(data['content'].replace('\n', '')).decode('utf-8')
        return data['sha'], decoded

    async def github_commit_push(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        sha: Optional[str] = None,
    ) -> str:
        payload = {
            'message': commit_message,
            'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
            'branch': config.GITHUB_BRANCH,
        }
        if sha:
            payload['sha'] = sha
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.put(
                self._file_url(file_path),
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
        return response.json()['commit']['html_url']


github_client = GitHubClient()