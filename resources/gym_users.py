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
    #update_queue_status(machine_groups, machines, machine_group_id)
    if groupQueue:
        if in_use == 'queued':
            if str(user_id) in groupQueue['queue']:
                queuedMachines = machines.count({'machine_group_id': machine_group_id, 'in_use': 'queued'})
                # ex: 2 machines available, user at 1 index of queue (second person) then allow checkin
                if groupQueue['queue'].index(str(user_id)) < queuedMachines:
                    # removing user from queue and allowing them to check in
                    remove_user(machine_groups, gym_users, machine_group_id, user_id)
                else:
                    # user too far in queue to be allowed next
                    validCheckin = False
            else:
                # user not in queue
                validCheckin = False
        elif in_use == 'open':
            # user was in the queue but when to an open machine instead of queued machine
            if str(user_id) in groupQueue['queue']:
                queuedMachines = machines.count({'machine_group_id': machine_group_id, 'in_use': 'queued'})
                # if a machine was queued for the user, then unqueue one machine
                if groupQueue['queue'].index(str(user_id)) < queuedMachines:
                    machines.update_one({'machine_group_id': machine_group_id, 'in_use': 'queued'},
                            {'$set': {'in_use': 'open'}},
                            upsert=True)
                remove_user(machine_groups, gym_users, machine_group_id, user_id)

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
        print(groupQueue['queue'])
        print(len(groupQueue['queue']))
        queuedMachines = machines.count({'machine_group_id': machine_group_id, 'in_use': 'queued'})
        print(queuedMachines)
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
                        status = m_checkout(self.gym_users, self.machines, user['_id'], machine['_id'])
                        return {'checkin': False, 'checkout': True, 'status': status}, 200
                    else:
                        # User already checked into different machine without checkout
                        m_checkout(self.gym_users, self.machines, user['_id'], ObjectId(gym_user['machine_id']))
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
