import flask
import json
from flask import request, jsonify, render_template, redirect, url_for
import pandas as pd
import os
from time import sleep
import numpy as np
import sqlite3
from ChoreTracker import utils
from apscheduler.schedulers.background import BackgroundScheduler


def daily_update():
    # Putting in a regular job to calculate the day's
    # scheduled/recurring chores  
    # check whether today's chores have already been added
    if len (utils.get_active_chores()) == 0:
        print("Scheduler is alive!")
        utils.update_choreinstances()
    else:
        print(f"Found {len(utils.get_active_chores())} chores for today")

sched = BackgroundScheduler(daemon=True)
sched.add_job(daily_update,'interval',hours=2)
sched.start()

daily_update()


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

@app.route('/')
def index(methods=['GET']):
    people = json.loads(utils.get_chore_counts_by_person().T.to_json())
    print("people:", people)
    return render_template('index.html', title='People with chores today', people = people)
    
@app.route('/showPersonChores')
def showPersonChores(methods=['GET']):
    if request.args.get('personId'):
        # should have personId and personName
        chores = json.loads(utils.get_person_chores(personId=request.args.get('personId')).T.to_json())
        print(chores)
        return render_template(
            'showPersonChores.html', 
            title=request.args.get('personName'), 
            chores = chores,
            personId = request.args.get('personId'),
            )
    else:
        return render_template(
            'error.html',
            pagename='showPersonChores',
            errorname='NoPersonIdError'
        )

@app.route('/completeChore')
def completeChore(methods=['GET']):
    if request.args.get('personId') and request.args.get('choreInstanceId'):
        # should have personId and choreInstanceId
        if utils.complete_chore_instance(
                personId=request.args.get('personId'),
                choreInstanceId=request.args.get('choreInstanceId')
            ):
            chores = json.loads(utils.get_person_chores(personId=request.args.get('personId')).T.to_json())
            # return redirect(url_for(f'showPersonChores?personId={request.args.get("personId")}&personName={request.args.get("personName")}')
            return render_template(
                'showPersonChores.html', 
                title=request.args.get('personName'), 
                chores = chores,
                personId = request.args.get('personId'),
                )
            
        else:
            # need to show an error page
            return render_template(
                'error.html',
                pagename='completeChore',
                errorname='UnableToCompleteChoreError'
            )

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