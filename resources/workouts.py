from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


# format of workouts document:
#       '_id'                           : ObjectId
#       'name'                          : String
#       'array_exercises_dictionary'    : Array (of Dictionaries)
#       'difficulty'                    : String
#       'workout_image'                 : String
#       'user_id'                       : ObjectId (String)


class Workouts(Resource):
    # set the collection to workouts
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.workouts = self.db['workouts']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('name', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('array_exercises_dictionary', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('difficulty', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('workout_image', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('user_id', required=False, location="form", case_sensitive=True, trim=True)

    # general get request to get workout(s)
    def get(self, query_category, query_key):
        
        # adjust the types accordingly since default is string
        if '_id' == query_category.lower():
            query_key = ObjectId(query_key)

        # send proper query / if they want all
        if query_category and query_key == 'all':
            result_cursor = self.workouts.find({})
        else:
            result_cursor = self.workouts.find({query_category : query_key})

        # in order to return a result needs to be {} format
        return_result = {}
        for document in result_cursor:
            # change all ObjectID's to str()
            for key, value in document.items():
                if '_id' == key.lower():
                    document[key] = str(value)
            
            # place the document in the result with the '_id' as the name
            return_result[document['_id']] = document

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result

    # manage post requests to the workouts collection
    # example: curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Squat","category":"Legs","machine_type_id":2,"reps":"12-15 reps","duration":"3 sets"}' http://localhost:5000/exercises
    def post(self):
        json_data = self.parser.parse_args()

        try:
            result = self.workouts.insert_one(json_data)
            return {'inserted': result.acknowledged}
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}
