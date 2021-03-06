from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


# format of machines document:
#       '_id'               : ObjectId
#       'name'              : String
#       'muscle_id'         : ObjectId (String)
#       'machine_group_id'  : ObjectId (String)
#       'station_id'        : String
#       'in_use'            : String ('open', 'queued', 'occupied')
#       'user_id'           : ObjectId (String)
#       'signed_in_time'    : String


class Machines(Resource):
    # set the collection to machines
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.machines = self.db['machines']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('name', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('muscle_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('machine_group_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('station_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('in_use', required=True, location="form", case_sensitive=True, trim=True)

    # general get request to get machine(s)
    def get(self, query_category, query_key):
        
        # adjust the types accordingly since default is string
        if '_id' == query_category.lower():
            query_key = ObjectId(query_key)
        if query_category == 'station_id':
            query_key = str(query_key)
        
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
                if '_id' == key.lower():
                    document[key] = str(value)
                if 'signed_in_time' == key.lower():
                    document[key] = str(value)
                if key == 'station_id':
                    document[key] = str(value)
            
            # place the document in the result with the '_id' as the name
            return_result[document['_id']] = document

        # if unable to find matching query item
        if return_result == {}:
            return_result = {'error:' : 'Not Found'}

        return return_result

    # manage post requests to the machines collection
    # example: curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Squat","category":"Legs","machine_type_id":2,"reps":"12-15 reps","duration":"3 sets"}' http://localhost:5000/exercises
    def post(self):
        json_data = self.parser.parse_args()

        try:
            result = self.machines.insert_one(json_data)
            return {'inserted': result.acknowledged}, 200
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}, 400


class MachinesStatus(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.machines = self.db['machines']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('station_list', type=list, required=True, location='json')

    # get machine status for LED color
    def get(self):
        args = self.parser.parse_args()
        station_list = args['station_list']
        cursor = self.machines.find({'station_id': {"$in": station_list}})
        result = {}
        for doc in cursor:
            result[doc['station_id']] = doc['in_use']
        return result, 200
