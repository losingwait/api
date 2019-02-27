from flask_restful import Resource, reqparse, abort

class Exercises(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['db']
        self.exercises = self.db['exercises']
    def get(self):
        return {'initial': 'commit'}, 200
