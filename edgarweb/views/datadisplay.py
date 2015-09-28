from .. import app

from ..forms import CompanyForm

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask.ext.login import login_required
from bokeh.plotting import figure
from bokeh.embed import components

import edgarweb.modules.pysec
from edgarweb.modules.pysec.util import company_utilities as cu

import pandas as pd

datadisplay = Blueprint('datadisplay',__name__,
                        template_folder = 'templates')

the_df = None
@datadisplay.route('/datadisplay',methods=['GET','POST'])
@login_required
def show_data():
    global the_df
    
    form = CompanyForm()
    
    script = None
    div    = None

    if form.validate_on_submit(): #no validation yet...
        
        if not isinstance(the_df,pd.DataFrame):
            the_df = cu.get_complete_df(form.ticker.data)
            
        plot = figure(x_axis_type = "datetime")
        plot.line(the_df.Date.values,
                  the_df.apply(cu.get_field,args=(form.value.data,),axis=1).values,
                  color='#1F78B4')

        
        script, div = components(plot)
        
    return render_template("datadisplay.html",
                           form   = form,
                           script = script,
                           div    = div)
