# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

from flask import Flask, render_template, request, jsonify

# [START gae_python37_datastore_store_and_fetch_times]
from google.cloud import datastore

datastore_client = datastore.Client("makeuoft-268321")

# [END gae_python37_datastore_store_and_fetch_times]
app = Flask(__name__)


# [START gae_python37_datastore_store_and_fetch_times]
def store_time(dt):
    entity = datastore.Entity(key=datastore_client.key('visit'))
    entity.update({
        'timestamp': dt
    })

    datastore_client.put(entity)


def fetch_times(limit):
    query = datastore_client.query(kind='visit')
    query.order = ['-timestamp']

    times = query.fetch(limit=limit)

    return times
# [END gae_python37_datastore_store_and_fetch_times]


def create_person(name, fob_id=""):
    entity = datastore.Entity(key=datastore_client.key('person'))
    entity.update({
        'name': name,
        'fob_id': fob_id,
        'state': 'SAFE',
        'location': 'UNKNOWN',
        'last_location': 'UNKNOWN'
    })
    datastore_client.put(entity)
    return entity


def get_all_persons():
    query = datastore_client.query(kind='person')
    query.order = ['name']
    persons = query.fetch()
    return persons


@app.route('/persons/<string:fob_id>/location', methods=["POST"])
def location_handler(fob_id):
    if request.method == "POST":
        query = datastore_client.query(kind='person')
        query.add_filter('fob_id', '=', fob_id)
        query.keys_only()
        person_key = list(query.fetch())[0].key
        content = request.get_json()
        room = content["room"]
        state = content["state"]
        person = datastore_client.get(person_key)
        if state == "OUT":
            person["last_location"] = room
            person["location"] = "UNKNOWN"
        elif state == "IN":
            person["last_location"] = person["location"]
            person["location"] = room
        datastore_client.put(person)
        return jsonify(datastore_client.get(person_key))


@app.route('/persons', methods=['GET', 'POST'])
def persons_handler():
    if request.method == 'POST':
        content = request.get_json()
        person = create_person(content["name"], content.get("fob_id", ""))
        return jsonify(person)
    else:
        persons = get_all_persons()
        persons = [person for person in persons]
        return jsonify(persons)


@app.route('/')
def root():
    # Store the current access time in Datastore.
    store_time(datetime.datetime.now())

    # Fetch the most recent 10 access times from Datastore.
    times = fetch_times(10)

    return render_template(
        'index.html', times=times)
# [END gae_python37_datastore_render_times]


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
