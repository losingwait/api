from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


# format of machines document:
#       '_id'               : ObjectId
#       'name'              : String
#       'muscle_id'         : ObjectId (String)
#       'machine_group_id'  : ObjectId (String)
#       'sensor_id'         : Int
#       'in_use'            : Boolean
#       'user_id'           : ObjectId (String)
#       'signed_in_time'    : String


class Machines(Resource):
    # set the collection to machines
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.machines = self.db['machines']

    # general get request to get machine(s)
    def get(self, query_category, query_key):
        
        # adjust the types accordingly since default is string
        if '_id' in query_category.lower():
            query_key = ObjectId(query_key)
        if query_category == 'sensor_id':
            query_key = int(query_key)
        if query_category == 'in_use':
            query_key = bool(query_key)
        
        # send proper query / if they want all
        if query_category and query_key == 'all':
            result_cursor = self.machines.find({})
        else:
            result_cursor = self.machines.find({query_category : query_key})

        # in order to return a result needs to be {} format
        return_result = {}
        for document in result_cursor:
            # change all ObjectID's to str()
            for key, value in document.items():
                if '_id' in key.lower():
                    document[key] = str(value)
                if key == 'sensor_id':
                    document[key] = int(value)
            
            # place the document in the result with the '_id' as the name
            return_result[document['_id']] = document

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result

    # manage post requests to the machines collection
    # example: curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Squat","category":"Legs","machine_type_id":2,"reps":"12-15 reps","duration":"3 sets"}' http://localhost:5000/exercises
    def post(self):
        json_data = request.get_json(force=True)

        try:
            result = self.machines.insert_one(json_data)
            return {'inserted': result.acknowledged}
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}

