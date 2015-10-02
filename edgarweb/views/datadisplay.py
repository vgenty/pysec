from .. import app

from ..forms import CompanyForm

from .. import tasks

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, jsonify
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

    script = None
    div    = None
    loaded = False
    
    if the_df is not None:
        loaded = True;

    form = CompanyForm()
    
    if request.method == 'GET':
        return render_template("datadisplay.html",
                               form   = form,
                               script = script,
                               div    = div,
                               dfloaded  = int(loaded))


    if request.method == 'POST':

        #VIC STOPPED HERE
        form.ticker.data = the_df.iloc[0,'Tick']
        
        if form.validate_on_submit(): #no validation yet...
            
            TOOLS = "pan,wheel_zoom,box_zoom,reset,resize,hover"
            choice = str(form.value.data)

            the_df[choice] = the_df.apply(cu.get_field,args=(choice,),axis=1)
            c = ColumnDataSource(the_df[['Date',choice,'DateStr']])

            plot = figure(x_axis_label = "Time",
                          y_axis_label = "Dollars ($)",
                          x_axis_type  = "datetime",
                          toolbar_location = "below",
                          tools=TOOLS)
            
            hover = plot.select(dict(type=HoverTool))
            hover.tooltips = [
                ("Amount:", "@%s"%choice),
                ("Date:",   "@DateStr"),
            ]
            
        
            plot.line   ('Date','Cash',color='#1F78B4',source=c)
            plot.scatter('Date','Cash',color='#1F78B4',source=c,size=10)
            
        
            script, div = components(plot)
        
        
        return render_template("datadisplay.html",
                               form      = form,
                               script    = script,
                               div       = div,
                               dfloaded  = loaded)
    
    # 

    #     res    = None
    #     result = None

    #     if not isinstance(the_df,pd.DataFrame):
    #         #flash something and try again
        
    #     TOOLS = "pan,wheel_zoom,box_zoom,reset,resize,hover"
        
    #     the_df[form.value.data] = the_df.apply(cu.get_field,args=(form.value.data,),axis=1)
    #     c = ColumnDataSource(the_df[['Date',form.value.data,'DateStr']])
        

    #     plot = figure(x_axis_label = "Time",
    #                   y_axis_label = "Dollars ($)",
    #                   x_axis_type  = "datetime",
    #                   toolbar_location = "below",
    #                   tools=TOOLS)
        
    #     hover = plot.select(dict(type=HoverTool))
    #     hover.tooltips = [
    #         ("Amount:", "@%s"%form.value.data),
    #         ("Date:",   "@DateStr"),
    #     ]
        
        
    #     plot.line   ('Date',form.value.data,color='#1F78B4',source=c)
    #     plot.scatter('Date',form.value.data,color='#1F78B4',source=c,size=10)
        
        
    #     script, div = components(plot)

    # # return redirect(url_for('datadisplay.show_data'))
    # return render_template("datadisplay.html",
    #                        form   = form,
    #                        script = script,
    #                        div    = div)

@datadisplay.route('/getdataframe/<ticker>', methods=['POST'])
def getdataframe(ticker):
    #result = tasks.get_data_frame_background.apply_async(args=[form.ticker.data])
    result = tasks.get_data_frame_background.apply_async(args=[ticker])
    return jsonify({}), 202, {'Location': url_for('datadisplay.resultstatus',
                                                  task_id = result.id) }


@datadisplay.route('/status/<task_id>')
def resultstatus(task_id):
    global the_df
    task = tasks.get_data_frame_background.AsyncResult(task_id)

    response = None
    if task.state == 'PENDING':
        response = {
            'state'  : task.state,
            'message': 'Task pending'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state'  : task.state,
            'message': task.info['message']
        }
    elif task.state == 'SUCCESS':
        # we need to tell someone we just got the full dataframe!!! although i hope we don't send this back to ajax
        # lets just set the_df to task.get(), then return success. Then once AJAX sees this lets let it take us back to
        # datadisplay view with post call? I don't know yet
        
        the_df = task.get()
        
        response = {
            'state'   : task.state,
            'message' : 'Complete',
            'result'  : 'Success'
        }
    elif task.state == 'FAILURE':
        response = {
            'state'  : task.state,
            'message': str(task.info['message']) #this is exception...
        }
    
    return jsonify(response)

