import flask
import json
from flask import request, jsonify
import pandas as pd
import os
from time import sleep
import numpy as np
import sqlite3
from ChoreTracker import utils
from apscheduler.schedulers.background import BackgroundScheduler


app = flask.Flask(__name__)
app.config['DEBUG'] = True


def ApiClass(function, *args, **kwargs):
    def wrapper(*args, **kwargs):
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=function.to_json(),
        )
    return wrapper

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

@app.route('/api/v1/resources/get_active_chore', methods=['GET'])
def dummy():
    pass


@app.route('/api/v1/resources/get_active_chores', methods=['GET'])
def get_active_chores():
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.get_active_chores().to_json(),
        )

dumm_func = ApiClass(utils.get_active_chores())