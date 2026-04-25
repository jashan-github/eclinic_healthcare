"""
Cron script: mark past webinars as completed (expired).

Run from the webinar project root, e.g.:
  cd /var/www/backend/webinar && python -m app.scripts.mark_expired_webinars

Cron example (every hour):
  0 * * * * cd /var/www/backend/webinar && /path/to/python -m app.scripts.mark_expired_webinars >> /var/log/webinar-mark-expired.log 2>&1
"""

import asyncio
import sys


async def main() -> int:
    from app.db.session import AsyncSessionLocal
    from app.services.webinar_service import WebinarService
    from app.core.logging import logger

    try:
        async with AsyncSessionLocal() as session:
            service = WebinarService(session)
            count = await service.mark_past_webinars_completed()
        logger.info(f"Mark expired webinars: {count} webinar(s) marked as completed.")
        print(f"OK: {count} webinar(s) marked as completed.")
        return 0
    except Exception as e:
        logger.exception("Mark expired webinars failed")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
