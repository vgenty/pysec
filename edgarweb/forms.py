from . import app

from flask_wtf import Form

from flask_wtf.file import FileField
from wtforms import SubmitField, TextField, PasswordField
from wtforms import validators, BooleanField, IntegerField

from wtforms.validators import ValidationError, NumberRange

import re

def allowed_file_types(ftypes): #fancy factory definition
    message = 'Allowed file types are' + str(ftypes)
    
    def _allowed_file_types(form, field):
        m = re.search(r'.([a-z]{3})$',field.data.filename)
        if m is None or m.group(1) not in ftypes:
            raise ValidationError(message)
        
    return _allowed_file_types

class LoginForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')
    submit   = SubmitField('Submit')
 

class ToPrintForm(Form):
    document = FileField('Document to Print',
                         validators=[validators.Required(),
                                     allowed_file_types(app.config['ALLOWED_FILE_TYPES'])])
    submit   = SubmitField('Submit')

    sides          = BooleanField('Double-sided',default=False)
    orientation    = BooleanField('Landscape'   ,default=False)
    
    copies = IntegerField("Copies",
                          validators=[validators.NumberRange(min=1,
                                                             max=50,
                                                             message='Max copies is 50')])

