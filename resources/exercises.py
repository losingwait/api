from flask_restful import Resource # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id

class Exercises(Resource):
    # set the collection to exercises
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.exercises = self.db['exercises']

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
