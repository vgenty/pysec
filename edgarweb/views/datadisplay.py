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
    
    form = CompanyForm()
    
    if request.method == 'GET':
            
        the_df = None
        loaded = 0;
        return render_template("datadisplay.html",
                               form   = form,
                               dfloaded  = int(loaded))
    
    
    if request.method == 'POST':
        loaded = 1;
        form.ticker.data = the_df.iloc[0]['Ticker']
        form.value.data  = None
        
        return render_template("datadisplay.html", #this requires a page reload which is not good...
                               form      = form,
                               dfloaded  = loaded)

@datadisplay.route('/getplot',methods=['POST'])
def getplot():
    global the_df
    #if 'choice' in request.form:
    
    # this is also really dumb
    # lets have javascript query this page for python script and div
    
    choice = request.form['choice']
    tckr   = the_df.iloc[0]['Ticker']
    
    #if form.validate_on_submit():
    # currently disabling validation, i will let javascript do most of the routing from now
    # on (i.e. client)
    
    TOOLS = "pan,wheel_zoom,box_zoom,reset,resize,hover"
    
        #at this point we should check choice and make sure tht it is
    #actually a valid XBRL but whatever maybe we just send
    #error status back to client
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
            

    plot.line   ('Date',choice,color='#1F78B4',source=c)
    plot.scatter('Date',choice,color='#1F78B4',source=c,size=10)
    
    script, div = components(plot)
    #return this somehow probably JSON
    return render_template("plot.html",script=script,div=div,tckr=tckr,choice=choice)
        
@datadisplay.route('/currentdfname')
def currentdfname():
    global the_df
    #print the_df.iloc[0]['Ticker']
    return jsonify({'df_name' : the_df.iloc[0]['Ticker']})
    
@datadisplay.route('/getdataframe/<ticker>', methods=['POST'])
def getdataframe(ticker):
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
            'message': 'Task pending',
            'percent': 0
        }
    elif task.state == 'PROGRESS':
        response = {
            'state'  : task.state,
            'message': task.info['message'],
            'percent': task.info['percent']
        }
    elif task.state == 'SUCCESS':
        # we need to tell someone we just got the full dataframe!!! although i hope we don't send this back to ajax
        # lets just set the_df to task.get(), then return success. Then once AJAX sees this lets let it take us back to
        # datadisplay view with post call? I don't know yet
        
        the_df = task.get()
        
        response = {
            'state'   : task.state,
            'message' : 'Complete',
            'result'  : 'Success',
            'percent'  : 100
        }
    elif task.state == 'FAILURE':
        response = {
            'state'  : task.state,
            'message': str(task.info['message']), #this is exception...
            'percent': 0
        }
    
    return jsonify(response)

