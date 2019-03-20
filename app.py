from flask import Flask, jsonify, render_template, request, redirect, url_for, g, session
from flask_restful import Api
from pymongo import MongoClient
from resources.users import SignUp, Login
from resources.exercises import Exercises
from resources.machines import Machines
from resources.archives import Archives
from resources.notes import Notes
from resources.workouts import Workouts
from resources.muscles import Muscles
from resources.machine_groups import MachineGroups
from resources.gym_users import GymUsers

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb+srv://nicholas_tiner:senior_design@csce483-dn7uw.mongodb.net/test-data?retryWrites=true")
db = client['wait-data']

# adding resources for get requests
api.add_resource(SignUp, '/users/signup', resource_class_kwargs={'db': db})
api.add_resource(Login, '/users/login', resource_class_kwargs={'db': db})
api.add_resource(Exercises, '/exercises/<string:query_category>/<string:query_key>', '/exercises', resource_class_kwargs={'db': db})
api.add_resource(Archives, '/archives/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Muscles, '/muscles/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Notes, '/notes/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(MachineGroups, '/machine_groups/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Machines, '/machines/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(Workouts, '/workouts/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(GymUsers, '/gym_users/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})

# function to get a usage message
@app.route('/help')
def help():
    help_message = '''
    {
        "help"                          : "The below information is how the general form of curl requests should be structured.",
        "format"                        : "/collection/search_item/key_value",
        "example"                       : "/exercises/muscle_id/1",
        "possible collections"          : "users, gym_users, exercises, archives, muscles, notes, machine_groups, machines, workouts",
        "users search items"            : "_id, name, password, email, rfid",
        "gym_users search items"        : "_id, name, check_in_time, check_out_time, machine_id",
        "exercises search items"        : "_id, name, muscle_id, machine_group_id, exercise_media, user_id (optional)",
        "archives search items"         : "_id, user_id, date, length, workout_id",
        "muscles search items"          : "_id, name, all",
        "notes search items"            : "_id, title, text, date, user_id",
        "machine_groups search items"   : "_id, name, location",
        "machines search items"         : "_id, name, muscle_id, machine_group_id, sensor_id, in_use, user_id, signed_in_time",
        "workouts search items"         : "_id, name, exercises_array, difficulty, workout_media, user_id"
    } \n'''
    return help_message

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/gym/status')
def gym_status():
    return render_template('gym/status.html')

@app.route('/register/user', methods=('GET', 'POST'))
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        rfid = request.form['rfid']
        # use this if email or rfid already exists
        # return redirect(url_for('register_user'))
        return redirect(url_for('home'))
    return render_template('register/user.html')

@app.route('/register/machine', methods=('GET', 'POST'))
def register_machine():
    if request.method == 'POST':
        pass
    return render_template('register/machine.html')

@app.route('/admin/login', methods=('GET', 'POST'))
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # actually log in here
        session.clear()
        session['user_id'] = "qwer123"
        return redirect(url_for('home'))
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('home'))

@app.before_request
def check_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        # actually call db here
        g.name = "Bobby"
        g.user = "123"

if __name__ == '__main__':
    #app.debug = True
    app.config['SECRET_KEY'] = 'senior_design_losing_wait'
    app.run()
