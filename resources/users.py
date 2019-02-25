from flask_restful import Resource, reqparse, abort

class Users(Resource):
    # gets all users
    def get(self):
        return {'initial': 'commit'}, 200
