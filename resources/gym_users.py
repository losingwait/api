from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


# format of gym_users document:
#       '_id'               : ObjectId
#       'name'              : String
#       'check_in_time'     : String
#       'check_out_time'    : String
#       'machine_id'        : ObjectId


class GymUsers(Resource):
    # set the collection to exercises
    def __init__(self, **kwargs):
        # setting the collection
        self.db = kwargs['db']
        self.exercises = self.db['gym_users']

    # general get request to get exercise(s)
    def get(self, query_category, query_key):

        # adjust the types accordingly since default is string
        if query_category == 'machine_type_id':
            query_key = int(query_key)
        if query_category == '_id':
            query_key = ObjectId(query_key)

        # in order to return a result needs to be {} format
        result_cursor = self.exercises.find({query_category : query_key})
        return_result = {}
        for document in result_cursor:
            document['_id'] = str(document['_id'])
            return_result[document['_id']] = document

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result

    # manage post requests to the exercises collection
    # example: curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Squat","category":"Legs","machine_type_id":2,"reps":"12-15 reps","duration":"3 sets"}' http://localhost:5000/exercises
    def post(self):
        json_data = request.get_json(force=True)

        try:
            result = self.exercises.insert_one(json_data)
            return {'inserted': result.acknowledged}
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}
