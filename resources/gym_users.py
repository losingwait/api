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


class GymUsers(Resource):
    # set the collection to workouts
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']

    # general get request to get workout(s)
    def get(self, query_category, query_key):
        
        # adjust the types accordingly since default is string
        if '_id' == query_category.lower():
            query_key = ObjectId(query_key)

        # send proper query / if they want all
        if query_category and query_key == 'all':
            result_cursor = self.gym_users.find({})
        else:
            result_cursor = self.gym_users.find({query_category : query_key})

        # in order to return a result needs to be {} format
        return_result = {}
        for document in result_cursor:
            # change all ObjectID's to str()
            for key, value in document.items():
                if '_id' == key.lower():
                    document[key] = str(value)
                if 'time' == key.lower():
                    document[key] = str(value)
            
            # place the document in the result with the '_id' as the name
            return_result[document['_id']] = document

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result

def g_checkin(gym_users, user):
    return gym_users.insert_one({'user_id': str(user['_id']), 'name': user['name'], 'time': datetime.now()})

def g_checkout(gym_users, machines, machine_groups, user_id, queueLocks):
    gym_user = gym_users.find_one({'user_id': str(user_id)})
    # Checkout of machine if user checked into machine
    if 'machine_id' in gym_user:
        m_checkout(gym_users, machines, machine_groups, ObjectId(gym_user['user_id']), ObjectId(gym_user['machine_id']), queueLocks)
    # Leave queue if user is in queue
    if 'current_queue' in gym_user:
        queueLocks.lockQueue(gym_user['current_queue'])
        remove_user(machine_groups, gym_users, machines, gym_user['current_queue'], gym_user['user_id'], True)
        queueLocks.unlockQueue(gym_user['current_queue'])
    return gym_users.delete_one({'user_id': str(gym_user['user_id'])})

def m_checkin(gym_users, machines, machine_groups, user_id, machine_id, queueLocks):
    machine = machines.find_one({'_id': ObjectId(machine_id)}, {'_id': 1, 'machine_group_id': 1, 'in_use': 1})
    queueLocks.lockQueue(machine['machine_group_id'])
    groupQueue = machine_groups.find_one({'_id': ObjectId(machine['machine_group_id'])}, {'queue': 1, '_id': 0})
    validCheckin = True
    if groupQueue:
        if machine['in_use'] == 'queued' or machine['in_use'] == 'occupied':
            in_queue, user_next_in_queue = remove_user(machine_groups, gym_users, machines, machine['machine_group_id'], user_id, False)
            if not in_queue or not user_next_in_queue:
                validCheckin = False
        elif machine['in_use'] == 'open':
            remove_user(machine_groups, gym_users, machines, machine['machine_group_id'], user_id, True)

    if validCheckin:
        userResult = gym_users.update_one({'user_id': str(user_id)},
            {'$set': {'machine_id': str(machine_id)}},
            upsert=False)
        machineResult = machines.update_one({'_id': ObjectId(machine_id)},
            {'$set': {'in_use': 'occupied', 'user_id': str(user_id), 'signed_in_time': datetime.now()}},
            upsert=False)
    queueLocks.unlockQueue(machine['machine_group_id'])
    return validCheckin

def m_checkout(gym_users, machines, machine_groups, user_id, machine_id, queueLocks):
    machine = machines.find_one({'_id': ObjectId(machine_id)}, {'_id': 1, 'machine_group_id': 1})
    queueLocks.lockQueue(machine['machine_group_id'])
    status = 'open'
    groupQueue = machine_groups.find_one({'_id': ObjectId(machine['machine_group_id'])}, {'queue': 1, '_id': 0})
    if groupQueue:
        queuedMachines = machines.count({'machine_group_id': str(machine['machine_group_id']), 'in_use': 'queued'})
        if len(groupQueue['queue']) > queuedMachines:
            status = 'queued'

    userResult = gym_users.update_one({'user_id': str(user_id)},
        {'$unset': {'machine_id': ""}},
        upsert=False)
    machineResult = machines.update_one({'_id': ObjectId(machine_id)},
        {'$set': {'in_use': status},
        '$unset': {'user_id': "", 'signed_in_time': ""}},
        upsert=False)
    queueLocks.unlockQueue(machine['machine_group_id'])
    return status

class GymCheckin(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.queueLocks = kwargs['queueLocks']
        self.gym_users = self.db['gym_users']
        self.users = self.db['users']
        self.machines = self.db['machines']
        self.machine_groups = self.db['machine_groups']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('rfid', required=True, location="form", case_sensitive=True, trim=True)

    # allows users to check into and out of a gym
    def post(self):
        args = self.parser.parse_args()
        user = self.users.find_one({'rfid': args['rfid']}, {'name': 1, '_id': 1})
        if user:
            gym_user = self.gym_users.find_one({'user_id': str(user['_id'])}, {'user_id': 1})
            if not gym_user:
                # check into the gym
                result = g_checkin(self.gym_users, user)
                return {'checkin': result.acknowledged, 'checkout': False}, 200
            else:
                # check out of the gym
                result = g_checkout(self.gym_users, self.machines, self.machine_groups, gym_user['user_id'], self.queueLocks)
                return {'checkin': False, 'checkout': result.acknowledged}, 200
        else:
            return {'error': 'user not registered'}, 400

class MachineCheckin(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.queueLocks = kwargs['queueLocks']
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
        machine = self.machines.find_one({'station_id': args['station_id']}, {'_id': 1, 'machine_group_id': 1, 'user_id': 1})
        if user and machine:
            gym_user = self.gym_users.find_one({'user_id': str(user['_id'])})
            if gym_user:
                if 'machine_id' not in gym_user:
                    # User in gym but not checked into machine
                    if m_checkin(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], self.queueLocks):
                        if 'user_id' in machine:
                            # Need to check out old user if they were already on machine
                            userResult = gym_users.update_one({'user_id': str(machine['user_id'])},
                                {'$unset': {'machine_id': ""}},
                                upsert=False)
                        return {'checkin': True, 'checkout': False, 'status': 'occupied'}, 200
                    else:
                        return {'error': 'user not in queue'}, 403
                else:
                    # TODO: Add archives here
                    if gym_user['machine_id'] == str(machine['_id']):
                        # User check out of current machine
                        status = m_checkout(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], self.queueLocks)
                        return {'checkin': False, 'checkout': True, 'status': status}, 200
                    else:
                        # User already checked into different machine without checkout
                        m_checkout(self.gym_users, self.machines, self.machine_groups, user['_id'], ObjectId(gym_user['machine_id']), self.queueLocks)
                        if m_checkin(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], self.queueLocks):
                            if 'user_id' in machine:
                                userResult = gym_users.update_one({'user_id': str(machine['user_id'])},
                                    {'$unset': {'machine_id': ""}},
                                    upsert=False)
                            return {'checkin': True, 'checkout': False, 'status': 'occupied'}, 200
                        else:
                            return {'error': 'user not in queue'}, 403
            else:
                # User wasn't checked into the gym
                g_checkin(self.gym_users, user)
                if m_checkin(self.gym_users, self.machines, self.machine_groups, user['_id'], machine['_id'], self.queueLocks):
                    if 'user_id' in machine:
                        userResult = gym_users.update_one({'user_id': str(machine['user_id'])},
                            {'$unset': {'machine_id': ""}},
                            upsert=False)
                    return {'checkin': True, 'checkout': False, 'status': 'occupied'}, 200
                else:
                    return {'error': 'user not in queue'}, 403
        else:
            return {'error': 'User or machine are not registered'}, 400

class FreeWeights(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.machines = self.db['machines']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('station_id', required=True, type=str, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('available', required=True, type=str, location="form", case_sensitive=True, trim=True)

    def post(self):
        args = self.parser.parse_args()
        machine = self.machines.find_one({'station_id': args['station_id']}, {'_id': 1, 'in_use': 1})
        if machine:
            if args['available'].lower() in ['true']:
                if machine['in_use'] != 'open':
                    # TODO: Add archives here
                    self.machines.update_one({'_id': ObjectId(machine['_id'])},
                        {'$set': {'in_use': 'open'},
                        '$unset': {'signed_in_time': ''}},
                        upsert=False)
                    return {'updated': True, 'status': 'open'}, 200
                else:
                    return {'updated': False, 'status': 'open'}, 200
            elif args['available'].lower() in ['false']:
                if machine['in_use'] != 'occupied':
                    self.machines.update_one({'_id': ObjectId(machine['_id'])},
                        {'$set': {'in_use': 'occupied', 'signed_in_time': datetime.now()}},
                        upsert=False)
                    return {'updated': True, 'status': 'occupied'}, 200
                else:
                    return {'updated': False, 'status': 'occupied'}, 200
            else:
                return {'error': 'Invalid available parameter. Should be true or false'}, 400
        else:
            return {'error': 'Free Weight Machine is not registered'}, 400
