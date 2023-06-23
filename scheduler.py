from pytz import utc
import os
# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# from apscheduler.executors.asyncio import AsyncIOExecutor


jobstores = {
    # 'mongo': {'type': 'mongodb'},
    'default': SQLAlchemyJobStore(url=os.environ.get('DATABASE_URL'))
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
