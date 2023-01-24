import flask
import json
from flask import request, jsonify
import pandas as pd
import os
from time import sleep
import numpy as np
import sqlite3
from ChoreTracker import utils

app = flask.Flask(__name__)
app.config['DEBUG'] = True


class JSON_Improved(json.JSONEncoder):
    '''
    Used to help jsonify numpy arrays or lists that contain numpy data types.
    '''
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(json.JSONEncoder, self).default(obj)

app.json_provider_class = JSON_Improved # json_encoder

@app.route('/api/v1/resources/get_chores', methods=['GET', 'POST'])
def do_something():
    if request.method == 'POST':
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.get_chores().to_json(),
        )
    else:
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.get_chores().to_json(),
        )


@app.route('/api/v1/resources/get_people', methods=['GET', 'POST'])
def get_people():
    return jsonify(
        isError=False, 
        message='Success', 
        statusCode=200, 
        results=utils.get_people().to_json(),
    )


@app.route('/api/v1/resources/get_chore_rate', methods=['GET', 'POST'])
def get_chore_rate():
    return jsonify(
        isError=False, 
        message='Success', 
        statusCode=200, 
        results=utils.get_chore_rate(),
    )

@app.route('/api/v1/resources/get_chore_rates', methods=['GET', 'POST'])
def get_chore_rates():
    return jsonify(
        isError=False, 
        message='Success', 
        statusCode=200, 
        results=utils.get_chore_rates().to_html(index=False),
    )


@app.route('/api/v1/resources/set_chore_rate', methods=['POST'])
def set_chore_rate():    
    if request.form.get('rate'):
        rate = float(request.form.get('rate'))
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.update_chore_rate(ChoreRate=rate),
        )
    else:
        return jsonify(
            isError=True, 
            message='No rate specified', 
            statusCode=500, 
        )
app.run(port=5000)