from flask import Flask
from flask_restful import Api
from pymongo import MongoClient
from resources.users import Users
from resources.exercises import Exercises
from resources.machines import Machines
from resources.archives import Archives
from resources.journals import Journals
from resources.workouts import Workouts

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb+srv://nicholas_tiner:senior_design@csce483-dn7uw.mongodb.net/test-data?retryWrites=true")
db = client['wait-data']

api.add_resource(Users, '/users/<string:email>', resource_class_kwargs={'db': db})
api.add_resource(Exercises, '/exercises/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})

if __name__ == '__main__':
    #app.debug = True
    app.run()