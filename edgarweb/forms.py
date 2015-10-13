from . import app

from flask_wtf import Form

#from flask_wtf.file import FileField
from wtforms import SubmitField, TextField, PasswordField, SelectField
from wtforms import validators, BooleanField, IntegerField

from wtforms.validators import ValidationError, NumberRange

class CompanyForm(Form):
    ticker = TextField  ( 'Ticker' )
    #value  = TextField  ( 'Value'  )
    value  = SelectField()

    submit = SubmitField( 'Fetch ' )
    series = SubmitField( 'Plot'   )
    

class LoginForm(Form):
    username = TextField    ( 'Username' )
    password = PasswordField( 'Password' )
    submit   = SubmitField  ( 'Submit'   )
 
