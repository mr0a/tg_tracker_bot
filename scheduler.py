from pytz import utc
import os
# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# from apscheduler.executors.asyncio import AsyncIOExecutor


db_url = os.environ.get(
    'DATABASE_URL', 'sqlite:///scheduler.sqlite')
jobstores = {
    # 'mongo': {'type': 'mongodb'},
    'default': SQLAlchemyJobStore(url=db_url.replace('postgres', 'postgresql'))
}
executors = {
    'default': {'class': 'apscheduler.executors.asyncio:AsyncIOExecutor'}
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
scheduler = AsyncIOScheduler()

# .. do something else here, maybe add jobs etc.

scheduler.configure(jobstores=jobstores, executors=executors,
                    job_defaults=job_defaults, timezone=utc)
