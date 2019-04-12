from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message
import sys


# format of machine_groups document:
#       '_id'               : ObjectId
#       'name'              : String
#       'location'          : Int
#       'queue'             : Array of User ID Strings (Optional)


# format of a post request to add / remove user from queue
# {
#     "_id": needed,
#     "user_id": needed,
#     "action": "add"/"remove"
# }

# add user to queue
def add_user(machine_groups, gym_users, machines, group_id, user_id):
    user = gym_users.find_one({'user_id': str(user_id)}, {'current_queue': 1})
    # if user isn't checked into gym
    if not user:
        return False
    # user already queued up
    if 'current_queue' in user: 
        remove_user(machine_groups, gym_users, machines, user['current_queue'], user_id, True)

    # check if queue already exists
    exists_find_result = machine_groups.find({"$and": [{"_id": ObjectId(group_id)}, {"queue": {"$exists": True }}]})
    exists_bool = bool(len(list(exists_find_result)))

    if not exists_bool: # create queue of one person
        result = machine_groups.update_one({'_id': ObjectId(group_id)},
                {'$set': {'queue': [str(user_id)]}},
                upsert=False)
    else: # add new user to end of array
        # get array from db
        queue_result = machine_groups.find({"_id": ObjectId(group_id)},{"queue": 1})
        queue_array = []
        for doc in queue_result:
            queue_array.append(doc)
        
        # get queue add append user to the end
        queue = list(queue_array[0]["queue"])
        queue.append(str(user_id))

        # update queue in db
        result = machine_groups.update_one({'_id': ObjectId(group_id)},
                {'$set': {'queue': queue}},
                upsert=False)

    # update gym user with queue and queue one machine if 'open'
    gym_users.update_one({'user_id': str(user_id)},
            {'$set': {'current_queue': str(group_id)}},
            upsert=False)
    # note that upsert if false, if no machines are open then no machine should change to queued
    machines.update_one({'machine_group_id': str(group_id), 'in_use': 'open'},
            {'$set': {'in_use': 'queued'}},
            upsert=False)

    return result.acknowledged

# remove user from queue
def remove_user(machine_groups, gym_users, machines, group_id, user_id, free_machine):
    # get array from db
    queue_result = machine_groups.find({"_id": ObjectId(group_id)},{"queue": 1})
    queue_array = []
    for doc in queue_result:
        queue_array.append(doc)
    
    if not queue_array or 'queue' not in queue_array[0]:
        return False, False
    # get queue remove user from it
    queue = list(queue_array[0]["queue"])
    user_position = sys.maxsize
    if str(user_id) in queue:
        user_position = queue.index(str(user_id))
        queue.remove(str(user_id))
    else:
        return False, False

    # update queue in db
    if len(queue) == 0:
        result = machine_groups.update_one({'_id': ObjectId(group_id)},
                {'$unset': {'queue': ''}},
                upsert=False)
    else:
        result = machine_groups.update_one({'_id': ObjectId(group_id)},
                {'$set': {'queue': queue}},
                upsert=False)

    gym_users.update_one({'user_id': str(user_id)},
            {'$unset': {'current_queue': ''}},
            upsert=False)
    queuedMachines = machines.count({'machine_group_id': str(group_id), 'in_use': 'queued'})
    user_next_in_queue = user_position < queuedMachines
    # if a machine could have been queued for the user, then unqueue one machine
    if free_machine and user_next_in_queue:
        # note that upsert if false, if no machines are queued then no machine should change to open
        machines.update_one({'machine_group_id': str(group_id), 'in_use': 'queued'},
                {'$set': {'in_use': 'open'}},
                upsert=False)

    return result.acknowledged, user_next_in_queue

class Queue(Resource):
    # set the collection to machine_groups
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.queueLocks = kwargs['queueLocks']
        self.machine_groups = self.db['machine_groups']
        self.gym_users = self.db['gym_users']
        self.machines = self.db['machines']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('user_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('action', required=True, location="form", case_sensitive=True, trim=True)

    # general get request to get the queue for a specific machine_group
    def get(self, search_group):
        
        result_cursor = self.machine_groups.find({"_id": ObjectId(search_group)})

        # in order to return a result needs to be {} format
        return_result = {}
        
        for document in result_cursor:
            return_result[document["name"]] = document["queue"]

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result
        
    # curl -i -H "Content-Type: application/json" -X POST -d '{"_id":"5c951d991c9d4400008f68e3","user_id":"123259","action":"add"}' http://localhost:5000/queue
    def post(self):
        json_data = self.parser.parse_args()

        try:
            if json_data['action'] == "add":
                self.queueLocks.lockQueue(json_data['_id'])
                result = add_user(self.machine_groups, self.gym_users, self.machines, json_data['_id'], json_data['user_id'])
                self.queueLocks.unlockQueue(json_data['_id'])
            elif json_data['action'] == "remove":
                self.queueLocks.lockQueue(json_data['_id'])
                result, user_next = remove_user(self.machine_groups, self.gym_users, self.machines, json_data['_id'], json_data['user_id'], True)
                self.queueLocks.unlockQueue(json_data['_id'])

            return {'updated': result}
        except pymongo.errors.DuplicateKeyError as e:
            return {'updated': False, 'error': e.details}