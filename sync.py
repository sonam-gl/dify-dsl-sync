"""
sync.py — Dify DSL to GitHub sync script.

Designed to run as a standalone cron job. No web server required.

Cron schedule examples (add to crontab with: crontab -e):
    0 2 * * *       python /path/to/sync.py          # daily at 02:00 UTC
    0 2,14 * * *    python /path/to/sync.py          # twice daily
    0 */6 * * *     python /path/to/sync.py          # every 6 hours
    0 8 * * 1-5     python /path/to/sync.py          # weekdays at 08:00 UTC

Environment variables (set in .env or as system env vars):
    DIFY_HOST            Dify Cloud URL (default: https://cloud.dify.ai)
    DIFY_ACCESS_TOKEN    Bearer token from browser DevTools Local Storage
    DIFY_APP_ID          UUID of the Dify app to export
    DIFY_APP_NAME        Short name used in commit messages
    GITHUB_TOKEN         Personal Access Token with repo scope
    GITHUB_OWNER         Repository owner or organisation
    GITHUB_REPO          Repository name
    GITHUB_BRANCH        Target branch (default: main)
    GITHUB_FILE_PATH     Destination path in repo (default: dsl/app.yml)

Exit codes:
    0  — committed or no_change (success)
    1  — error or token_expired (failure — cron will log to syslog)
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone

from sync_service import sync_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


async def main() -> int:
    started_at = datetime.now(timezone.utc).isoformat()
    log.info('Dify DSL sync started — %s', started_at)

    result = await sync_service.run()

    log.info('Status        : %s', result.status)
    log.info('Committed     : %s', result.committed)
    log.info('Message       : %s', result.message)

    if result.committed:
        log.info('Commit URL    : %s', result.commit_url)
        log.info('Lines changed : %d', result.lines_changed)

    if result.status == 'token_expired':
        log.error(
            'ACTION REQUIRED: DIFY_ACCESS_TOKEN has expired.\n'
            '  1. Go to https://cloud.dify.ai and log in.\n'
            '  2. Open DevTools > Application > Local Storage > access_token.\n'
            '  3. Copy the value and update DIFY_ACCESS_TOKEN in your .env file.\n'
            '  4. Re-run this script to verify.'
        )
        return 1

    if result.status == 'error':
        log.error('Sync failed: %s', result.message)
        return 1

    log.info('Sync complete.')
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))