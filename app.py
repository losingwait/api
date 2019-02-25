from flask import Flask
from flask_restful import Api
from pymongo import MongoClient
from resources.users import Users

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb+srv://nicholas_tiner:senior_design@csce483-dn7uw.mongodb.net/test-data?retryWrites=true")
db = client['wait-data']

api.add_resource(Users, '/users')

if __name__ == '__main__':
    #app.debug = True
    app.run()
