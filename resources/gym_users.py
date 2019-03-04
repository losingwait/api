from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message
from datetime import datetime

# format of gym_users document:
#       '_id'               : ObjectId
#       'name'              : String
#       'check_in_time'     : String
#       'check_out_time'    : String
#       'machine_id'        : ObjectId

class Checkin(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']
        self.users = self.db['users']
        self.machines = self.db['machines']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('user_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('machine_id', required=False, location="form", case_sensitive=True, trim=True)

    # allows users to check into gym
    def post(self):
        args = self.parser.parse_args()
        user = self.users.find_one({'_id': ObjectId(args['user_id'])}, {'name': 1, '_id': 0})
        try:
            result = self.gym_users.insert_one({'user_id': ObjectId(args['user_id']), 'name': user['name'], 'time': datetime.now()})
            return {'inserted': result.acknowledged}, 201
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}, 400

    # allows users to check a machine
    def put(self):
        args = self.parser.parse_args()
        try:
            result = self.gym_users.update_one({'user_id': ObjectId(args['user_id'])},
                {'$set': {'machine_id': ObjectId(args['machine_id'])}},
                upsert=False)
            return {'updated': result.acknowledged}, 202
        except pymongo.errors.DuplicateKeyError as e:
            return {'updated': False, 'error': e.details}, 400

class Checkout(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']
        self.users = self.db['users']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('user_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('machine_id', required=False, location="form", case_sensitive=True, trim=True)

    # allows users to check out of gym
    def delete(self):
        args = self.parser.parse_args()
        print(args['user_id'])
        return {}, 201

    # allows users to check out of a machine
    def put(self):
        args = self.parser.parse_args()
        print(args['user_id'])
        print(args['machine_id'])
        return {}, 202
