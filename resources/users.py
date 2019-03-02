from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message

# format of users document:
#       '_id'               : ObjectId
#       'name'              : String
#       'password'          : String
#       'email'             : String
#       'RFID'              : Int

class Login(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.users = self.db['users']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('email', required=True, location="form", case_sensitive=False, trim=True)

    # gets one user
    def post(self):
        args = self.parser.parse_args()
        cursor = self.users.find_one({'email': args['email']})
        cursor['_id'] = str(cursor['_id'])
        return cursor, 200

class SignUp(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.users = self.db['users']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('name', required=True, location="form", case_sensitive=False, trim=True)
        self.parser.add_argument('email', required=True, location="form", case_sensitive=False, trim=True)

    # sign up
    def post(self, **kwargs):
        args = self.parser.parse_args()
        try:
            result = self.users.insert_one(args)
            return {'inserted': result.acknowledged}, 200 
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}, 400
