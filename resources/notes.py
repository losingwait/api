from flask import request # need request to do post request
from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message


# format of notes document:
#       '_id'               : ObjectId
#       'title'             : String
#       'text'              : String
#       'date'              : String
#       'user_id'           : ObjectId (String)


class Notes(Resource):
    # set the collection to notes
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.notes = self.db['notes']

    # general get request to get note(s)
    def get(self, query_category, query_key):
        
        # adjust the types accordingly since default is string
        if '_id' == query_category.lower():
            query_key = ObjectId(query_key)
        
        # send proper query / if they want all
        if query_category and query_key == 'all':
            result_cursor = self.notes.find({})
        else:
            result_cursor = self.notes.find({query_category : query_key})

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

    # manage post requests to the notes collection
    # example: curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Squat","category":"Legs","machine_type_id":2,"reps":"12-15 reps","duration":"3 sets"}' http://localhost:5000/exercises
    def post(self):
        json_data = request.get_json(force=True)

        try:
            result = self.notes.insert_one(json_data)
            return {'inserted': result.acknowledged}
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}
