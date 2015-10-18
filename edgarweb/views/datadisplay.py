from .. import app

from ..forms import CompanyForm

from .. import tasks

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, jsonify
from flask.ext.login import login_required

from bokeh.plotting import figure
from bokeh.embed    import components
from bokeh.models   import HoverTool, ColumnDataSource, CustomJS, TapTool

import pandas as pd

from edgarweb.modules.pysec.util import company_utilities as cu

import json

#temporary
import edgarweb.modules.pysec
from   edgarweb.modules.pysec.util import company_utilities as cu
#/temporary

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
        form.value.choices = [ (0,'') ]
        return render_template("datadisplay.html",
                               form   = form,
                               dfloaded  = int(loaded))
    
    
    if request.method == 'POST':
        loaded = 1;
        form.ticker.data = the_df.iloc[0]['Ticker']
        form.value.choices = [ (key,key) for key in the_df.iloc[0]['xbrl'].fields ]
        
        return render_template("datadisplay.html", #this requires a page reload which is not good...
                               form      = form,
                               dfloaded  = loaded)


#
# Various URLS for javascript to query and get result
#

@datadisplay.route('/getplot',methods=['POST'])
def getplot():
    global the_df

    choice = request.form['choice']
    tckr   = the_df.iloc[0]['Ticker']
        
    TOOLS = "pan,wheel_zoom,box_zoom,reset,resize,hover,tap"
    
    # at this point we should check choice and make sure tht it is
    # actually a valid XBRL but whatever maybe we just send
    # error status back to client somehow
    
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


    plot.line   ('Date',choice,color='#1F78B4',source=c,name="line")
    plot.scatter('Date',choice,color='#1F78B4',source=c,size=10,name="scatter")

    # renderer = plot.select(name="line")[0]
    # renderer.nonselection_glyph=renderer.glyph.clone()

    renderer = plot.select(name="scatter")[0]
    renderer.nonselection_glyph = renderer.glyph.clone()

    
    #we need call back function to stupid.js
    code = """ 
var ind = cb_obj.get('selected')['1d'].indices;
        hhh(ind);
           """
    
    taptool = plot.select(dict(type=TapTool))
    print taptool
    
    callback = CustomJS(args={'source':c}, code=code)
    
    # hover.callback=callback
    taptool.callback=callback

    #Change me!!!!
    taptool.names = ["scatter"]
    
    script, div = components(plot)

    #return this somehow probably JSON
    return render_template("plot.html",script=script,div=div,tckr=tckr,choice=choice)


@datadisplay.route('/currentdfratios/<i>')
def currentdfratios(i): # ratios already calculated when this is called
    global the_df
    print "im here..."
    print i
    i = int(i)
    
    #temporary
    the_df = cu.calculate_ratios(the_df)
    #/temporary
    print ""
    print ""
    print ""
    xxx = the_df.iloc[i]['Ratios']
    print ""
    print ""
    print ""
    # jjj = json.dumps(xxx)
    # print jjj
    print ""
    print ""
    return jsonify(xxx)

@datadisplay.route('/currentdfname')
def currentdfname():
    global the_df
    return jsonify({'df_name' : the_df.iloc[0]['Ticker']})


#######################
# Celery Tasks
#
@datadisplay.route('/calcratios',methods=['POST'])
def calcratios():
    global the_df
    result = tasks.calculate_ratios.apply_async(args=[the_df])
    return jsonify({}), 202, {'Location': url_for('datadisplay.resultstatus',
                                                  task_id = result.id) }
    
@datadisplay.route('/getdataframe/<ticker>', methods=['POST'])
def getdataframe(ticker):
    result = tasks.get_data_frame_background.apply_async(args=[ticker])
    return jsonify({}), 202, {'Location': url_for('datadisplay.resultstatus',
                                                  task_id = result.id) }
#######################
# Celery status display
#
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

