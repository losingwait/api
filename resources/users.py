from flask_restful import Resource, reqparse, abort

class Users(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.users = self.db['users']

    # gets all users
    def get(self, email):
        cursor = self.users.find_one({'email': email}, {'_id': False})
        return cursor, 200
