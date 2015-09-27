from .. import app
from .. import login_manager

from ..forms import LoginForm
from ..users import User, UserNotFoundError

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort

from flask.ext.login import login_user

import os

login = Blueprint('login',__name__,
                  template_folder = 'templates')


#Various classes and methods

def next_is_valid(next):
    return True
            
@login_manager.user_loader
def load_user(id):
    return User.get(id)

# Views
@login.route('/')
def index():
    return redirect(url_for('.login_to_submit'))
    
@login.route('/login',methods=['GET','POST'])
def login_to_submit():
    form = LoginForm()
    if form.validate_on_submit():

        user = User.get(form.username.data)

        if (user and user.password == form.password.data):
            login_user(user)
        else:
            flash(u'Contact Vic for User/Pass')
            return redirect(url_for('.login_to_submit'))

        # Not sure what this does...
        next = request.args.get('next')
        
        if not next_is_valid(next):
            return abort(400)
        return redirect(next or url_for('upload.upload_to_server'))


    return render_template('login.html', form=form)

