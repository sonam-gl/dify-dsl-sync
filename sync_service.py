import difflib
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from dify_client import dify_client, TokenExpiredError
from github_client import github_client
from config import config


@dataclass
class SyncResult:
    status: str                       # committed | no_change | token_expired | error
    committed: bool
    message: str
    commit_url: Optional[str]         = None
    lines_changed: int                = 0
    token_refresh_required: bool      = False


class SyncService:

    def _commit_message(self, app_name: str, diff_lines: list, custom: str = None) -> str:
        if custom:
            return custom
        added   = sum(1 for l in diff_lines if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in diff_lines if l.startswith('-') and not l.startswith('---'))
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        return f'chore: sync Dify DSL [{app_name}] +{added}/-{removed} ({ts})'

    def _diff(self, current: str, new: str) -> tuple:
        a = current.strip().splitlines()
        b = new.strip().splitlines()
        lines = list(difflib.unified_diff(a, b, fromfile='current', tofile='new', lineterm=''))
        changed = sum(
            1 for l in lines
            if l.startswith(('+', '-')) and not l.startswith(('+++', '---'))
        )
        return bool(lines), lines, changed

    async def run(
        self,
        app_id: str = None,
        file_path: str = None,
        commit_message: str = None,
        include_secret: bool = False,
    ) -> SyncResult:
        app_id    = app_id    or config.DIFY_APP_ID
        file_path = file_path or config.GITHUB_FILE_PATH

        try:
            new_dsl = await dify_client.export_dsl(app_id, include_secret)
        except TokenExpiredError as exc:
            return SyncResult(
                status='token_expired', committed=False,
                message=str(exc), token_refresh_required=True,
            )
        except Exception as exc:
            return SyncResult(status='error', committed=False,
                              message=f'DSL export failed: {exc}')

        try:
            sha, current_dsl = await github_client.get_file(file_path)
        except Exception as exc:
            return SyncResult(status='error', committed=False,
                              message=f'GitHub read failed: {exc}')

        if current_dsl is not None:
            changed, diff_lines, n_changed = self._diff(current_dsl, new_dsl)
            if not changed:
                return SyncResult(status='no_change', committed=False,
                                  message='DSL unchanged — no commit required.',
                                  lines_changed=0)
        else:
            diff_lines, n_changed = [], new_dsl.count('\n') + 1

        msg = self._commit_message(config.DIFY_APP_NAME, diff_lines, commit_message)
        try:
            url = await github_client.github_commit_push(file_path, new_dsl, msg, sha)
        except Exception as exc:
            return SyncResult(status='error', committed=False,
                              message=f'GitHub commit failed: {exc}')

        return SyncResult(status='committed', committed=True,
                          message=msg, commit_url=url, lines_changed=n_changed)


sync_service = SyncService()