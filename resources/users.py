from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message
from werkzeug.security import generate_password_hash, check_password_hash
from resources.gym_users import g_checkout

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
        self.parser.add_argument('password', required=True, location="form", case_sensitive=False, trim=True)

    # gets one user
    def post(self):
        args = self.parser.parse_args()
        cursor = self.users.find_one({'email': args['email']})
        if cursor:
            if check_password_hash(cursor['password'], args['password']):
                response = {}
                response['_id'] = str(cursor['_id'])
                response['name'] = cursor['name']
                response['email'] = cursor['email']
                return response, 200
        return {'ok': False}, 401

class SignUp(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.users = self.db['users']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('name', required=True, location="form", case_sensitive=False, trim=True)
        self.parser.add_argument('email', required=True, location="form", case_sensitive=False, trim=True)
        self.parser.add_argument('password', required=True, location="form", case_sensitive=False, trim=True)
        self.parser.add_argument('rfid', required=True, location="form", case_sensitive=False, trim=True)

    # sign up
    def post(self):
        args = self.parser.parse_args()
        try:
            args['password'] = generate_password_hash(args['password'], method='sha256')
            result = self.users.insert_one(args)
            return {'inserted': result.acknowledged}, 200 
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}, 400

class UpdateUser(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.queueLocks = kwargs['queueLocks']
        self.users = self.db['users']
        self.gym_users = self.db['gym_users']
        self.machines = self.db['machines']
        self.machine_groups = self.db['machine_groups']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('email', required=True, location="form", case_sensitive=False, trim=True)
        self.parser.add_argument('password', required=True, location="form", case_sensitive=False, trim=True)
        self.parser.add_argument('rfid', required=True, location="form", case_sensitive=False, trim=True)

    # gets one user
    def post(self):
        args = self.parser.parse_args()
        user = self.users.find_one({'email': args['email']}, {'_id': 1, 'password': 1})
        if user:
            gym_user = self.gym_users.find_one({'user_id': str(user['_id'])})
            # need to check a user out of the gym before updating
            if gym_user:
                g_checkout(self.gym_users, self.machines, self.machine_groups, gym_user['user_id'], self.queueLocks)
            if check_password_hash(user['password'], args['password']):
                try:
                    self.users.update_one({'email': args['email']},
                        {'$set': {'rfid': args['rfid']}},
                        upsert=False)
                    return {'updated': True}, 200
                except pymongo.errors.DuplicateKeyError as e:
                    return {'updated': False, 'error': 'Rfid already taken'}, 400
        return {'updated': False, 'error': 'User or password is invalid'}, 400
