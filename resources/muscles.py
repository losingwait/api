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

    # general get request to get categorie(s)
    def get(self, query_category, query_key):

        # adjust the types accordingly since default is string
        if query_category == '_id':
            query_key = ObjectId(query_key)

        # in order to return a result needs to be {} format
        result_cursor = self.muscles.find({query_category : query_key})
        return_result = {}
        for document in result_cursor:
            document['_id'] = str(document['_id'])
            return_result[document['_id']] = document

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result
