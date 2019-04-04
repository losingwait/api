from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


# format of muscles document:
#       '_id'               : ObjectId
#       'name'              : String


class Muscles(Resource):
    # set the collection to muscles
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.muscles = self.db['muscles']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('name', required=True, location="form", case_sensitive=True, trim=True)

    # general get request to get categorie(s)
    def get(self, query_category, query_key):

        # adjust the types accordingly since default is string
        if query_category == '_id':
            query_key = ObjectId(query_key)

        # send proper query
        if query_category and query_key == 'all':
            result_cursor = self.muscles.find({})
        else:
            result_cursor = self.muscles.find({query_category : query_key})

        # in order to return a result needs to be {} format
        return_result = {}
        for document in result_cursor:
            document['_id'] = str(document['_id'])
            return_result[document['_id']] = document

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result

    # manage post requests to the muscles collection
    # example: curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Squat","category":"Legs","machine_type_id":2,"reps":"12-15 reps","duration":"3 sets"}' http://localhost:5000/exercises
    def post(self):
        json_data = self.parser.parse_args()

        try:
            result = self.muscles.insert_one(json_data)
            return {'inserted': result.acknowledged}
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}