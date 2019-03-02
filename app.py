from flask import Flask, jsonify
from flask_restful import Api
from pymongo import MongoClient
from resources.users import Users
from resources.exercises import Exercises
from resources.machines import Machines
from resources.archives import Archives
from resources.journals import Journals
from resources.workouts import Workouts
from resources.categories import Categories
from resources.machine_types import MachineTypes

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb+srv://nicholas_tiner:senior_design@csce483-dn7uw.mongodb.net/test-data?retryWrites=true")
db = client['wait-data']
exercises = db['exercises']

# adding resources for get requests
api.add_resource(Users, '/users/<string:email>', resource_class_kwargs={'db': db})
api.add_resource(Exercises, '/exercises/<string:query_category>/<string:query_key>', '/exercises', resource_class_kwargs={'db': db})
api.add_resource(Archives, '/archives/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Categories, '/categories/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Journals, '/journals/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(MachineTypes, '/machine_types/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Machines, '/machines/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Workouts, '/workouts/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})

# function to get a usage message
@app.route('/help')
def help():
    help_message = '''
    {
        "help" : "The below information is how the general form of curl requests should be structured.",
        "format" : "/collection/search_item/key_value",
        "example" : "/exercises/category/Chest",
        "possible collections" : "users, exercises, archives, categories, journals, machine_types, machines, workouts",
        "users search items" : "tbd",
        "exercises search items" : "tbd",
        "archives search items" : "tbd",
        "categories search items" : "tbd",
        "journals search items" : "tbd",
        "machine_types search items" : "tbd",
        "machines search items" : "tbd",
        "workouts search items" : "tbd"
    } \n'''
    return help_message

if __name__ == '__main__':
    #app.debug = True
    app.run()