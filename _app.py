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

@app.route('/api/v1/resources/get_active_chores', methods=['GET'])
def get_active_chores():
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.get_active_chores().to_json(),
        )

@app.route('/api/v1/resources/get_chores', methods=['GET'])
def get_chores():
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.get_chores().to_json(),
        )


@app.route('/api/v1/resources/update_choreinstances', methods=['POST'])
def update_choreinstances():
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.update_choreinstances(),
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

@app.route('/api/v1/resources/get_chore_counts_by_person', methods=['GET', 'POST'])
def get_chore_counts_by_person():
    return jsonify(
        isError=False, 
        message='Success', 
        statusCode=200, 
        results=utils.get_chore_counts_by_person() # .to_json(),
    )

@app.route('/api/v1/resources/get_person_chores', methods=['GET', 'POST'])
def get_person_chores():

    if request.args.get('personId'):
        print(request.args.get('personId'))
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.get_person_chores(personId=request.args.get('personId')),
        )
        
    else:
        return jsonify(
            isError=True, 
            message='Error: No Person ID found', 
            statusCode=500
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


@app.route('/api/v1/resources/complete_chore_instance', methods=['POST'])
def complete_chore_instance():    
    if request.args.get('choreInstanceId'):
        ChoreInstanceId = int(request.args.get('choreInstanceId'))
        PersonId = int(request.args.get('personId'))
        print(f"Marking {ChoreInstanceId} complete")
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.complete_chore_instance(chore_instance_id=ChoreInstanceId, person_id=PersonId),
        )
    else:
        return jsonify(
            isError=True, 
            message='No ChoreInstanceId specified', 
            statusCode=500, 
        )
        
@app.route('/api/v1/resources/get_chores_table', methods=['GET', 'POST'])
def get_chores_table():    
    return utils.get_chores_table()
    
@app.route('/api/v1/resources/get_full_chores_table', methods=['GET', 'POST'])
def get_full_chores_table():    
    return utils.get_full_chores_table()

@app.route('/api/v1/resources/get_earnings_table', methods=['GET', 'POST'])
def get_earnings_table():    
    return utils.get_earnings_table()

@app.route('/api/v1/resources/uncomplete_chore_instance', methods=['POST'])
def uncomplete_chore_instance():    
    if request.args.get('choreInstanceId'):
        ChoreInstanceId = int(request.args.get('choreInstanceId'))
        return jsonify(
            isError=False, 
            message='Success', 
            statusCode=200, 
            results=utils.uncomplete_chore_instance(chore_instance_id=ChoreInstanceId),
        )
    else:
        return jsonify(
            isError=True, 
            message='No ChoreInstanceId specified', 
            statusCode=500, 
        )

#def create_chore(
#    name: str = None,
#    schedule: str = '1D',
#    start_date: dt.date = dt.date.today(),
#    start_time: dt.time = dt.time(7),
#    window: str = '4H',
#    repeats: bool = True,
#    active: bool = True,

def check_var(var):
    if not var is None:
        if len(var) == 0:
            # convert empty responses to default values
            return None
        elif var == 'on':
            # handle checkboxes
            return True
    return var

@app.route('/api/v1/resources/create_chore', methods=['POST'])
def create_chore(): 
    error=False   
    print(request.form)
    if request.form.get('name'):
        # check_var converts values to defaults
        # or expected values
        ChoreName = check_var(request.form.get('name'))
        ChoreSchedule = check_var(request.form.get('schedule'))
        ChoreStartDate = check_var(request.form.get('start_date'))
        ChoreStartTime = check_var(request.form.get('start_time'))
        ChoreWindow = check_var(request.form.get('window'))
        ChoreRepeats = check_var(request.form.get('repeats'))
        ChoreActive = check_var(request.form.get('active'))

        print('ChoreName: ', ChoreName)
        print('ChoreSchedule: ', ChoreSchedule)
        print('ChoreStartDate: ', ChoreStartDate)
        print('ChoreStartTime: ', ChoreStartTime)
        print('ChoreWindow: ', ChoreWindow)
        print('ChoreRepeats: ', ChoreRepeats)
        print('ChoreActive: ', ChoreActive)

        results=utils.create_chore(
            name=ChoreName,
            schedule=ChoreSchedule,
            start_date=ChoreStartDate,
            start_time=ChoreStartTime,
            window=ChoreWindow,
            repeats=ChoreRepeats,
            active=ChoreActive,
            )
        if results:
            return jsonify(
                isError=False, 
                message='Success', 
                statusCode=200,
                results=results
            )
        else:
            error=True
    else:
        print("Didn't get name")
        error=True

    if error:
        return jsonify(
            isError=True, 
            message='Error creating chore', 
            statusCode=500, 
            results=False
        )
    else:
        print(f"error not set: {error}")
        return jsonify(
            isError=True, 
            message='Error creating chore', 
            statusCode=500,  
            results=False
        )

app.run(port=5000)