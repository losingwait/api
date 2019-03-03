# api
Api to hit mongodb

Example "get" request: 
curl -i http://127.0.0.1:5000/muscles/name/Chest
curl -i http://127.0.0.1:5000/muscles/_id/5c7ae3211c9d440000aefae4

Example "post" request: 
curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Squat","category":"Legs","machine_type_id":2,"reps":"12-15 reps","duration":"3 sets"}' http://localhost:5000/exercises

# helpful resources
tutorial on basic flask restful:
https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask

tutorial on py mongo api:
http://api.mongodb.com/python/current/tutorial.html

tutorial on py mongo cursor object:
http://api.mongodb.com/python/current/api/pymongo/cursor.html#pymongo.cursor.Cursor

tutorial on reqparse for flask restful:
https://flask-restful.readthedocs.io/en/0.3.5/reqparse.html
