"""Bug 3: the periodic scrape job must actually be scheduled, not added paused."""

import asyncio

from src.scheduler import jobs


def test_scrape_job_is_scheduled_on_an_interval():
    async def first_run_time():
        scheduler = jobs.build_scheduler()
        scheduler.start()
        try:
            (job,) = scheduler.get_jobs()
            return job.next_run_time
        finally:
            scheduler.shutdown(wait=False)

    # APScheduler 3 treats next_run_time=None as "paused": the job would never fire.
    assert asyncio.run(first_run_time()) is not None
