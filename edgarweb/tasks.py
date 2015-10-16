from . import app
from . import celery

import edgarweb.modules.pysec
from   edgarweb.modules.pysec.util import company_utilities as cu

@celery.task(bind=True)
def get_data_frame_background(self,data):
    return cu.get_complete_df(data,celery_obj=self)


@celery.task(bind=True)
def calculate_ratios(self,df):
    return cu.calculate_ratios(df,celery_obj=self)
