from ..      import app
from ..forms import ToPrintForm

from flask import Blueprint, render_template, session, request
from flask.ext.login import login_required
from werkzeug import secure_filename

from ..extern import printer

upload = Blueprint('upload',__name__,
                   template_folder = 'templates')

    
printer = printer.Printer()

@upload.route('/upload',methods=['GET','POST'])
@login_required
def upload_to_server():

    filename = None
    form     = ToPrintForm()
    
    if request.method == 'GET':
        form.copies.data = 1
        
    if form.validate_on_submit():
        filename = secure_filename(form.document.data.filename)
        form.document.data.save(app.config['UPLOAD_FOLDER'] + filename)
        
        #session['filename'] = filename #put filename in the damn cookie! (No necessary?)
        
        printer.send(location    = app.config['UPLOAD_FOLDER'],
                     filename    = filename,
                     doublesided = form.sides.data,
                     landscape   = form.orientation.data,
                     copies      = form.copies.data)
        

    return render_template('upload.html', form=form, filename=filename)
