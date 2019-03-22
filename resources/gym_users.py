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
            gym_user = self.gym_users.find_one({'user_id': str(user['_id'])})
            if not gym_user:
                # check into the gym
                result = self.gym_users.insert_one({'user_id': str(user['_id']), 'name': user['name'], 'time': datetime.now()})
                return {'checkin': result.acknowledged, 'checkout': False}, 201
            else:
                # check out of the gym
                # TODO: May want to force check them out of a machine
                result = self.gym_users.delete_one({'user_id': str(user['_id'])})
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
        machine = self.machines.find_one({'station_id': args['station_id']}, {'_id': 1})
        print("user", user)
        print("machine", machine)
        if user and machine:
            gym_user = self.gym_users.find_one({'user_id': str(user['_id'])})
            if gym_user:
                if 'machine_id' not in gym_user:
                    # check into a machine
                    userResult = self.gym_users.update_one({'user_id': str(user['_id'])},
                        {'$set': {'machine_id': str(machine['_id'])}},
                        upsert=True)
                    machineResult = self.machines.update_one({'_id': machine['_id']},
                        {'$set': {'in_use': True, 'user_id': str(user['_id']), 'signed_in_time': datetime.now()}},
                        upsert=True)
                    return {'checkin': True, 'checkout': False}, 200
                else:
                    userResult = self.gym_users.update_one({'user_id': str(user['_id'])},
                        {'$unset': {'machine_id': ""}},
                        upsert=True)
                    machineResult = self.machines.update_one({'_id': machine['_id']},
                        {'$set': {'in_use': False},
                        '$unset': {'user_id': "", 'signed_in_time': ""}},
                        upsert=True)
                    # TODO: Add archives here
                    return {'checkin': False, 'checkout': True}, 200
            else:
                # TODO: May want to force check them in
                return {'error': "User not checked in"}, 401
        else:
            return {'error': "User or machine are not registered"}, 400
