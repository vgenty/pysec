from .. import app

from ..forms import CompanyForm

from .. import tasks

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask.ext.login import login_required

from bokeh.plotting import figure
from bokeh.embed    import components
from bokeh.models   import HoverTool, ColumnDataSource

import pandas as pd

from edgarweb.modules.pysec.util import company_utilities as cu

datadisplay = Blueprint('datadisplay',__name__,
                        template_folder = 'templates')

the_df = None

@datadisplay.route('/datadisplay',methods=['GET','POST'])
@login_required
def show_data():
    global the_df
    global the_plot
    
    form = CompanyForm()
    
    script = None
    div    = None

    if form.validate_on_submit(): #no validation yet...

        res    = None
        result = None
        aho = tasks.hi.delay()
        print aho.get()
        
        if not isinstance(the_df,pd.DataFrame):
            result = tasks.get_data_frame_background.apply_async(args=[form.ticker.data])
            the_df = result.get() #wait for task finish?
            #res    = result.collect()
        
        TOOLS = "pan,wheel_zoom,box_zoom,reset,resize,hover"

        #print res
        #print result.get()

        
        the_df[form.value.data] = the_df.apply(cu.get_field,args=(form.value.data,),axis=1)
        c = ColumnDataSource(the_df[['Date',form.value.data,'DateStr']])
        

        plot = figure(x_axis_label = "Time",
                      y_axis_label = "Dollars ($)",
                      x_axis_type  = "datetime",
                      toolbar_location="below",
                      tools=TOOLS)
        
        hover = plot.select(dict(type=HoverTool))
        hover.tooltips = [
            ("Amount:", "@%s"%form.value.data),
            ("Date:",   "@DateStr"),
        ]
        
        
        plot.line   ('Date',form.value.data,color='#1F78B4',source=c)
        plot.scatter('Date',form.value.data,color='#1F78B4',source=c,size=10)
        
        
        script, div = components(plot)
        
    return render_template("datadisplay.html",
                           form   = form,
                           script = script,
                           div    = div)
