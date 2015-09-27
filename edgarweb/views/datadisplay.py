from .. import app

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort

from flask.ext.login import login_required

datadisplay = Blueprint('datadisplay',__name__,
                        template_folder = 'templates')



@datadisplay.route('/datadisplay',methods=['GET','POST'])
@login_required
def show_data():

    return render_template('datadisplay.html')
