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

# add user to queue
def add_user(machine_groups, group_id, user_id):
    # check if queue already exists
    exists_find_result = machine_groups.find({"$and": [{"_id": ObjectId(group_id)}, {"queue": {"$exists": True }}]})
    exists_bool = bool(len(list(exists_find_result)))

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

    return result

# remove user from queue
def remove_user(machine_groups, group_id, user_id):
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

    return result

class Queue(Resource):
    # set the collection to machine_groups
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.machine_groups = self.db['machine_groups']

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
                result = add_user(self.machine_groups, json_data['_id'], json_data['user_id'])
            elif json_data['action'] == "remove":
                result = remove_user(self.machine_groups, json_data['_id'], json_data['user_id'])

            return {'updated': result.acknowledged}
        except pymongo.errors.DuplicateKeyError as e:
            return {'updated': False, 'error': e.details}