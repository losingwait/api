from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


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

# update queue to make sure 
'''def update_queue_status(machine_groups, machines, machine_group_id):
    groupQueue = machine_groups.find_one({'_id': ObjectId(machine_group_id)}, {'queue': 1, '_id': 0})['queue']
    availableMachines = machines.find({'machine_group_id': machine_group_id}, {'in_use': 1, '_id': 1})
    print(len(groupQueue))
    m_status = {}
    m_status['open'] = 0
    m_status['queued'] = 0
    m_status['occupied'] = 0
    for doc in availableMachines:
        print(doc)
        #m_status[doc['in_use']] += 1
    print(m_status)
    # their are more users in the queue then queued machines
    if len(groupQueue) > m_status['queued']:
        # if any machines are currently open
        if m_status['open']:
            need_queued_count = len(groupQueue) - m_status['queued']
            # Queue as many machines as possible & needed
            for doc in availableMachines:
                if doc['in_use'] == 'open':
                    machines.update_one({'_id': doc['_id']},
                            {'$set': {'in_use': 'queued'}},
                            upsert=True)
                    need_queued_count -= 1
                    if need_queued_count <= 0:
                        break
    # their are less users in the queue then queued machines
    elif len(groupQueue) < m_status['queued']:
        need_open_count = m_status['queued'] - len(groupQueue)
        for doc in availableMachines:
            if doc['in_use'] == 'queued':
                machines.update_one({'_id': doc['_id']},
                        {'$set': {'in_use': 'open'}},
                        upsert=True)
                need_open_count -=1
                if need_open_count <= 0:
                    break
    return'''

# add user to queue
def add_user(machine_groups, gym_users, group_id, user_id):
    # check if queue already exists
    exists_find_result = machine_groups.find({"$and": [{"_id": ObjectId(group_id)}, {"queue": {"$exists": True }}]})
    exists_bool = bool(len(list(exists_find_result)))

    user = gym_users.find_one({'user_id': str(user_id)}, {'current_queue': 1})
    # if user isn't checked into gym
    if not user:
        return False
    # user already queued up
    if 'current_queue' in user: 
        remove_user(machine_groups, gym_users, user['current_queue'], user_id)

    if not exists_bool: # create queue of one person
        result = machine_groups.update_one({'_id': ObjectId(group_id)},
                {'$set': {'queue': [str(user_id)]}},
                upsert=True)
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
                upsert=True)

    # add current queue to gym user
    gym_users.update_one({'user_id': str(user_id)}, {'$set': {'current_queue': str(group_id)}})
    # TODO: Check that at least one machine is queued status

    return result.acknowledged

# remove user from queue
def remove_user(machine_groups, gym_users, group_id, user_id):
    # get array from db
    queue_result = machine_groups.find({"_id": ObjectId(group_id)},{"queue": 1})
    queue_array = []
    for doc in queue_result:
        queue_array.append(doc)
    
    # get queue remove user from it
    queue = list(queue_array[0]["queue"])
    queue.remove(str(user_id))

    # update queue in db
    if len(queue) == 0:
        result = machine_groups.update_one({'_id': ObjectId(group_id)},
                {'$unset': {'queue': ''}},
                upsert=True)
    else:
        result = machine_groups.update_one({'_id': ObjectId(group_id)},
                {'$set': {'queue': queue}},
                upsert=True)

    gym_users.update_one({'user_id': str(user_id)}, {'$unset': {'current_queue': ''}})

    return result.acknowledged

class Queue(Resource):
    # set the collection to machine_groups
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.machine_groups = self.db['machine_groups']
        self.gym_users = self.db['gym_users']

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
        json_data = request.get_json(force=True)

        try:
            if json_data['action'] == "add":
                result = add_user(self.machine_groups, self.gym_users, json_data['_id'], json_data['user_id'])
            elif json_data['action'] == "remove":
                result = remove_user(self.machine_groups, self.gym_users, json_data['_id'], json_data['user_id'])

            return {'updated': result}
        except pymongo.errors.DuplicateKeyError as e:
            return {'updated': False, 'error': e.details}