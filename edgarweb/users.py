from . import app

from flask.ext.login import UserMixin

class UserNotFoundError(Exception):
    pass

class User(UserMixin): #Inherit from UsrMixin class
    
    '''Single User'''
    user  = app.config['UPLOAD_USER']
    pword = app.config['UPLOAD_PASS']

    USERS = { user : pword }
    
    def __init__(self, id):
        if not id in self.USERS:
            raise UserNotFoundError()
        self.id = id
        self.password = self.USERS[id]
        
    @classmethod
    def get(self_class, id):
        '''Return user instance of id, return None if not exist'''
        try:
            return self_class(id)
        except UserNotFoundError:
            return None
