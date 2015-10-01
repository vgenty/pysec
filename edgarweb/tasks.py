from . import app
from . import celery

import edgarweb.modules.pysec
from   edgarweb.modules.pysec.util import company_utilities as cu

@celery.task
def get_data_frame_background(data):
    return cu.get_complete_df(data)

@celery.task
def hi():
    return 'Hi'
