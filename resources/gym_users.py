from flask_restful import Resource, reqparse # our class must be of type Resource
from bson.objectid import ObjectId # needed to convert object id string back to type object id
import pymongo # needed to display error message

# format of gym_users document:
#       '_id'               : ObjectId
#       'name'              : String
#       'check_in_time'     : String
#       'check_out_time'    : String
#       'machine_id'        : ObjectId

class Checkin(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('user_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('machine_id', required=False, location="form", case_sensitive=True, trim=True)

    # allows users to check into gym
    def post(self):
        args = self.parser.parse_args()
        print(args['user_id'])
        return {}, 201

    # allows users to check a machine
    def put(self):
        args = self.parser.parse_args()
        print(args['user_id'])
        print(args['machine_id'])
        return {}, 202

class Checkout(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.gym_users = self.db['gym_users']
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('user_id', required=True, location="form", case_sensitive=True, trim=True)
        self.parser.add_argument('machine_id', required=False, location="form", case_sensitive=True, trim=True)

    # allows users to check out of gym
    def post(self):
        args = self.parser.parse_args()
        print(args['user_id'])
        return {}, 201

    # allows users to check out of a machine
    def put(self):
        args = self.parser.parse_args()
        print(args['user_id'])
        print(args['machine_id'])
        return {}, 202
