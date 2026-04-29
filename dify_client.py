import httpx
from config import config


class TokenExpiredError(Exception):
    """Raised when Dify Cloud returns HTTP 401 — DIFY_ACCESS_TOKEN has expired."""
    pass


class DifyClient:

    def _get_headers(self) -> dict:
        if not config.DIFY_ACCESS_TOKEN:
            raise ValueError(
                'DIFY_ACCESS_TOKEN is not set. Extract it from cloud.dify.ai '
                'DevTools > Application > Local Storage > access_token.'
            )
        return {
            'Authorization': f'Bearer {config.DIFY_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        }

    async def export_dsl(self, app_id: str, include_secret: bool = False) -> str:
        url = f'{config.DIFY_HOST}/console/api/apps/{app_id}/export'
        params = {'include_secret': str(include_secret).lower()}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 401:
            raise TokenExpiredError(
                'TOKEN_EXPIRED: update DIFY_ACCESS_TOKEN in .env from '
                'cloud.dify.ai DevTools > Application > Local Storage > access_token.'
            )
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        return response.json().get('data', response.text) if 'json' in content_type else response.text


dify_client = DifyClient()