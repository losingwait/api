from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message
from datetime import datetime
from resources.queue import remove_user

# format of gym_users document:
#       '_id'               : ObjectId
#       'name'              : String
#       'check_in_time'     : String
#       'check_out_time'    : String
#       'machine_id'        : ObjectId (String)

def g_checkin(gym_users, user):
    return gym_users.insert_one({'user_id': str(user['_id']), 'name': user['name'], 'time': datetime.now()})

def m_checkin(gym_users, machines, machine_groups, user_id, machine_id, machine_group_id, in_use):
    groupQueue = machine_groups.find_one({'_id': ObjectId(machine_group_id)}, {'queue': 1, '_id': 0})
    validCheckin = True
    if groupQueue:
        if in_use == 'queued':
            in_queue, user_next_in_queue = remove_user(machine_groups, gym_users, machines, machine_group_id, user_id, False)
            if not in_queue or not user_next_in_queue:
                validCheckin = False
        elif in_use == 'open':
            remove_user(machine_groups, gym_users, machines, machine_group_id, user_id, True)

    if validCheckin:
        userResult = gym_users.update_one({'user_id': str(user_id)},
            {'$set': {'machine_id': str(machine_id)}},
            upsert=True)
        machineResult = machines.update_one({'_id': machine_id},
            {'$set': {'in_use': 'occupied', 'user_id': str(user_id), 'signed_in_time': datetime.now()}},
            upsert=True)
    return validCheckin

def m_checkout(gym_users, machines, machine_groups, user_id, machine_id, machine_group_id):
    status = 'open'
    groupQueue = machine_groups.find_one({'_id': ObjectId(machine_group_id)}, {'queue': 1, '_id': 0})
    if groupQueue:
        queuedMachines = machines.count({'machine_group_id': machine_group_id, 'in_use': 'queued'})
        if len(groupQueue['queue']) > queuedMachines:
            status = 'queued'

    userResult = gym_users.update_one({'user_id': str(user_id)},
        {'$unset': {'machine_id': ""}},
        upsert=True)
    machineResult = machines.update_one({'_id': machine_id},
        {'$set': {'in_use': status},
        '$unset': {'user_id': "", 'signed_in_time': ""}},
        upsert=True)
    return status

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
                result = g_checkin(self.gym_users, user)
                return {'checkin': result.acknowledged, 'checkout': False}, 200
            else:
                # check out of the gym
                # TODO: Need to remove user from a queue if their in one, check current_queue in gym user
                if 'machine_id' in gym_user:
                    m_checkout(self.gym_users, self.machines, user['_id'], ObjectId(gym_user['machine_id']))
                result = self.gym_users.delete_one({'user_id': str(user['_id'])})
                return {'checkin': False, 'checkout': result.acknowledged}, 200
        else:
            return {'error': 'user not registered'}, 400

class MachineCheckin(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']
        self.users = self.db['users']
        self.machines = self.db['machines']
        self.machine_groups = self.db['machine_groups']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('rfid', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('station_id', required=True, location="form", case_sensitive=True, trim=True)

    # allows users to check into a machine
    def post(self):
        args = self.parser.parse_args()
        user = self.users.find_one({'rfid': args['rfid']}, {'name': 1, '_id': 1})
        machine = self.machines.find_one({'station_id': args['station_id']}, {'_id': 1, 'machine_group_id': 1, 'in_use': 1})
        if user and machine:
            gym_user = self.gym_users.find_one({'user_id': str(user['_id'])})
            if gym_user:
                if 'machine_id' not in gym_user:
                    # User in gym but not checked into machine
                    if m_checkin(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], machine['machine_group_id'], machine['in_use']):
                        return {'checkin': True, 'checkout': False, 'status': 'occupied'}, 200
                    else:
                        return {'error': 'user not in queue'}, 403
                else:
                    # TODO: Add archives here
                    if gym_user['machine_id'] == str(machine['_id']):
                        # User check out of current machine
                        status = m_checkout(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], machine['machine_group_id'])
                        return {'checkin': False, 'checkout': True, 'status': status}, 200
                    else:
                        # User already checked into different machine without checkout
                        old_m = self.machines.find_one({'_id': ObjectId(gym_user['machine_id'])}, {'_id': 1, 'machine_group_id': 1, 'in_use': 1})
                        m_checkout(self.gym_users, self.machines, self.machine_groups, user['_id'], old_m['_id'], old_m['machine_group_id'])
                        if m_checkin(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], machine['machine_group_id'], machine['in_use']):
                            return {'checkin': True, 'checkout': False, 'status': 'occupied'}, 200
                        else:
                            return {'error': 'user not in queue'}, 403
            else:
                # User wasn't checked into the gym
                g_checkin(self.gym_users, user)
                if m_checkin(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], machine['machine_group_id'], machine['in_use']):
                    return {'checkin': True, 'checkout': False, 'status': 'occupied'}, 200
                else:
                    return {'error': 'user not in queue'}, 403
        else:
            return {'error': 'User or machine are not registered'}, 400
