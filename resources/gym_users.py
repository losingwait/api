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

class GymCheckin(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']
        self.users = self.db['users']
        self.machines = self.db['machines']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('rfid', required=True, location="form", case_sensitive=True, trim=True)

    # allows users to check into and out of a gym
    def post(self):
        args = self.parser.parse_args()
        user = self.users.find_one({'rfid': args['rfid']}, {'name': 1, '_id': 1})
        if user:
            gym_user = self.gym_users.find_one({'user_id': ObjectId(user['_id'])})
            if not gym_user:
                # check into the gym
                result = self.gym_users.insert_one({'user_id': ObjectId(user['_id']), 'name': user['name'], 'time': datetime.now()})
                return {'checkin': result.acknowledged, 'checkout': False}, 201
            else:
                # check out of the gym
                result = self.gym_users.delete_one({'user_id': ObjectId(user['_id'])})
                return {'checkin': False, 'checkout': result.acknowledged}, 201
        else:
            return {'error': 'user not registered'}, 400

class MachineCheckin(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']
        self.users = self.db['users']
        self.machines = self.db['machines']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('rfid', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('station_id', required=True, location="form", case_sensitive=True, trim=True)

    # allows users to check into a machine
    def post(self):
        args = self.parser.parse_args()
        user = self.users.find_one({'rfid': args['rfid']}, {'_id': 1})
        machines = self.machines.find_one({'station_id': args['station_id']}, {'_id': 1})
        try:
            result = self.gym_users.update_one({'user_id': user['_id']},
                {'$set': {'machine_id': ObjectId(machines['_id'])}},
                upsert=False)
            return {'updated': result.acknowledged}, 202
        except pymongo.errors.DuplicateKeyError as e:
            return {'updated': False, 'error': e.details}, 400

# TODO: Split this into two classes
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
