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
        self.parser.add_argument('name', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('description', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('array_exercises_dictionary', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('difficulty', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('workout_image', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('user_id', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('action', required=False, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('del_id', required=False, location="form", case_sensitive=True, trim=True)

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
    # example: curl -i -H "Content-Type: application/json" -X POST -d '{"del_id":"5cb8aa20bf09a3000a2136d1","action":"remove"}' http://localhost:5000/workouts
    def post(self):
        json_data = request.get_json(force = True)
    
        try:
            if json_data['action'] == 'remove':
                result = self.workouts.delete_one({'_id' : ObjectId(json_data['del_id'])})
                return {'deleted': result.acknowledged}
            else:
                result = self.workouts.insert_one(json_data)
                return {'inserted': result.acknowledged}
        except pymongo.errors.DuplicateKeyError as e:
            return {'inserted': False, 'error': e.details}

#curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Karsen","array_exercises_dictionary":[{"_id":"5c9902a09aa5f3000a297201","name":"Cat Cow","reps":"10","sets":"1"},{"_id":"5c9902a09aa5f3000b0e0536","name":"Scapular Push-Up","reps":"10","sets":"1"},{"_id":"5c9902a19aa5f3000b0e0537","name":"Side-Lying Thoracic Rotation","reps":"5","sets":"1"},{"_id":"5c9902a19aa5f3000b0e0538","name":"Spider Crawl","reps":"50ft","sets":"3"},{"_id":"5c9902a19aa5f3000b0e0539","name":"Skip","reps":"50ft","sets":"3"},{"_id":"5c9902a19aa5f3000b0e053a","name":"Lateral Shuffle","reps":"50ft","sets":"3"},{"_id":"5c9902a29aa5f3000b0e053b","name":"Push-Ups","reps":"8","sets":"4"},{"_id":"5c9902a29aa5f3000b0e053c","name":"Floor Angel","reps":"10","sets":"4"},{"_id":"5c9902a29aa5f3000b0e053d","name":"Inverted Row","reps":"8","sets":"4"},{"_id":"5c9902a29aa5f3000b0e053e","name":"Childs Pose","reps":"1","sets":"4"},{"_id":"5c9902a29aa5f3000b0e053f","name":"Single-Leg Squat To Box","reps":"6","sets":"4"},{"_id":"5c9902a39aa5f3000a297202","name":"Hollow Hold","reps":"20 seconds","sets":"4"}],"difficulty":"Beginner","workout_image":"https://www.bodybuilding.com/images/2018/january/total-body-strong-sales-page-header-1920x1080-700xh.jpg"}' http://127.0.0.1:5000/workouts