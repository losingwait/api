from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


# format of users document:
#       '_id'               : ObjectId
#       'name'              : String
#       'password'          : String
#       'email'             : String
#       'RFID'              : Int


class Users(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.users = self.db['users']

    # gets all users
    def get(self, email):
        cursor = self.users.find_one({'email': email}, {'_id': False})
        return cursor, 200