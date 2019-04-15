from flask import Flask, jsonify, render_template, request, redirect, url_for, g, session, flash
from flask_restful import Api
from pymongo import MongoClient
import requests
from werkzeug.security import check_password_hash
from functools import wraps
from bson.objectid import ObjectId

from resources.users import SignUp, Login, UpdateUser
from resources.exercises import Exercises
from resources.machines import Machines, MachinesStatus
from resources.archives import Archives
from resources.notes import Notes
from resources.workouts import Workouts
from resources.muscles import Muscles
from resources.machine_groups import MachineGroups
from resources.gym_users import GymCheckin, MachineCheckin, GymUsers, FreeWeights
from resources.queue import Queue
from common.QueueLocks import QueueLocks

app = Flask(__name__)
api = Api(app)

app.secret_key = 'senior_design_losing_wait'

client = MongoClient("mongodb+srv://nicholas_tiner:senior_design@csce483-dn7uw.mongodb.net/test-data?retryWrites=true")
db = client['wait-data']

queueLocks = QueueLocks()

# adding resources for get requests
api.add_resource(SignUp, '/users/signup', resource_class_kwargs={'db': db})
api.add_resource(Login, '/users/login', resource_class_kwargs={'db': db})
api.add_resource(UpdateUser, '/users/update', resource_class_kwargs={'db': db, 'queueLocks': queueLocks})
api.add_resource(Exercises, '/exercises/<string:query_category>/<string:query_key>', '/exercises', resource_class_kwargs={'db': db})
api.add_resource(Archives, '/archives/<string:query_category>/<string:query_key>', '/archives', resource_class_kwargs={'db': db})
api.add_resource(Muscles, '/muscles/<string:query_category>/<string:query_key>', '/muscles', resource_class_kwargs={'db': db})
api.add_resource(Notes, '/notes/<string:query_category>/<string:query_key>', '/notes', resource_class_kwargs={'db': db})
api.add_resource(MachineGroups, '/machine_groups/<string:query_category>/<string:query_key>', '/machine_groups', resource_class_kwargs={'db': db})
api.add_resource(Machines, '/machines/<string:query_category>/<string:query_key>', '/machines', resource_class_kwargs={'db': db})
api.add_resource(MachinesStatus, '/machines/status', resource_class_kwargs={'db': db})
api.add_resource(Workouts, '/workouts/<string:query_category>/<string:query_key>', '/workouts', resource_class_kwargs={'db': db})
api.add_resource(GymUsers, '/gym_users/<string:query_category>/<string:query_key>', resource_class_kwargs={'db': db})
api.add_resource(GymCheckin, '/gym_users/checkin', resource_class_kwargs={'db': db, 'queueLocks': queueLocks})
api.add_resource(MachineCheckin, '/machine_users/checkin', resource_class_kwargs={'db': db, 'queueLocks': queueLocks})
api.add_resource(Queue, '/queue/<string:search_group>', '/queue', resource_class_kwargs={'db': db, 'queueLocks': queueLocks})
api.add_resource(FreeWeights, '/free_weights/status', resource_class_kwargs={'db': db})

# function to get a usage message
@app.route('/help')
def help():
    help_message = '''
    {
        "help"                          : "The below information is how the general form of curl requests should be structured.",
        "format"                        : "/collection/search_item/key_value",
        "example"                       : "/muscles/name/Chest",
        "possible collections"          : "users, gym_users, exercises, archives, muscles, notes, machine_groups, machines, workouts",
        "users search items"            : "_id, name, password, email, rfid",
        "gym_users search items"        : "_id, name, check_in_time, check_out_time, machine_id",
        "exercises search items"        : "_id, name, muscle_id, machine_group_id, exercise_media, user_id (optional)",
        "archives search items"         : "_id, user_id, date, length, workout_id",
        "muscles search items"          : "_id, name",
        "notes search items"            : "_id, title, text, date, user_id",
        "machine_groups search items"   : "_id, name, location",
        "machines search items"         : "_id, name, muscle_id, machine_group_id, sensor_id, in_use, user_id, signed_in_time",
        "workouts search items"         : "_id, name, array_exercises_array, difficulty, workout_image, user_id"
    } \n'''
    return help_message

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/gym/status')
@login_required
def gym_status():
    machine_groups = db['machine_groups'].find({})
    machines = db['machines'].find({})
    machine_stats = {}
    for machine in machines:
        if machine['machine_group_id'] not in machine_stats:
            machine_stats[machine['machine_group_id']] = {}
            machine_stats[machine['machine_group_id']]['total'] = 1
        else:
            machine_stats[machine['machine_group_id']]['total'] += 1
        if machine['in_use'] not in machine_stats[machine['machine_group_id']]:
            machine_stats[machine['machine_group_id']][machine['in_use']] = 1
        else:
            machine_stats[machine['machine_group_id']][machine['in_use']] += 1
    return render_template('gym/status.html', machine_groups=machine_groups, machine_stats=machine_stats)

@app.route('/register/machine', methods=('GET', 'POST'))
@login_required
def register_machine():
    if request.method == 'POST':
        name = request.form['name']
        muscle_id = request.form['muscle']
        machine_group_id = request.form['group']
        station_id = request.form['station']
        in_use = 'open'
        payload = {'name': name, 'muscle_id': muscle_id, 'machine_group_id': machine_group_id, 'station_id': station_id, 'in_use': in_use}
        r = requests.post(request.url_root + 'machines', data=payload)
        if r.status_code == requests.codes.ok:
            flash("You've created new a machine!", "success")
        else:
            flash("You've failed to create a new machine! Check the Mac Address!", "error")
        return redirect(url_for('register_machine'))
    else:
        # GET Request
        machines = db['machines'].find({})
        muscles = db['muscles'].find({}, {'name': 1, '_id': 1})
        machine_groups = db['machine_groups'].find({}, {'name': 1, '_id': 1})
        return render_template('register/machine.html', machines=machines, muscles=muscles, machine_groups=machine_groups)

@app.route('/admin/login', methods=('GET', 'POST'))
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = db['admins'].find_one({'email': email})
        if admin:
            if check_password_hash(admin['password'], password):
                session.clear()
                session['user_id'] = str(admin['_id'])
                flash("You've been logged in!", "success")
                return redirect(url_for('home'))
        flash("You couldn't be logged in!", "error")
        return redirect(url_for('admin_login'))
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
        admin = db['admins'].find_one({'_id': ObjectId(user_id)})
        if admin:
            g.name = admin['name']
            g.user = True
        else:
            session.clear()
            g.user = None

if __name__ == '__main__':
    app.debug = True
    app.run()
