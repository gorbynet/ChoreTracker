##
## Windows CLI:
## flask --app new_app.py --debug run --host=0.0.0.0
##

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
    if len (utils.get_todays_chores()) == 0:
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
    # print("people:", people)
    return render_template('index.html', title='People with chores today', people = people)
    
@app.route('/showPersonChores')
def showPersonChores(methods=['GET']):
    if request.args.get('personId'):
        # should have personId and personName
        chores = json.loads(utils.get_person_chores(personId=request.args.get('personId')).T.to_json())
        # print(chores)
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


@app.route('/createChore', methods=['GET'])
def createChore():
    return render_template("createChore.html", title="Create new chore")

@app.route('/createChoreAction', methods=['POST'])
def createChoreAction():
    result = request.form
    json_result = dict(result)
    
    # need to validate and then add this chore to the chores table  
    """
    name: str = None,
    schedule: str = '1D',
    start_date: dt.date = dt.date.today(),
    start_time: dt.time = dt.time(7),
    window: str = '4H',
    repeats: bool = True,
    active: bool = True,
    """
    # {'choreName': 'Test chore', 'schedule': '2D', 'startDate': '2023-02-28', 'start_time': '07:00', 'window': '4H', 'responsible': ''}
    for cbox in ['repeats', 'active']:
        if cbox in json_result:
            json_result[cbox] = True
        else:
            json_result[cbox] = False

    if utils.create_chore(
            name=json_result['choreName'],
            schedule=json_result['schedule'],
            start_date=json_result['startDate'],
            start_time=json_result['start_time'],
            window=json_result['window'],
            repeats=json_result['repeats'],
            active=json_result['active'],
        ):
        # assume chore is going to be the last one created 
        # with the specified name, and therefore have the highest ChoreId
        chores_df=utils.get_chores()
        ChoreId=chores_df[chores_df['name'] == json_result['choreName']]['ChoreID'].max()
        # chore_details = utils.get_chore_details(ChoreId=ChoreId).to_json()
        # people = utils.get_people().T.to_json()
        # print(ChoreId, chore_details, people)
        return redirect(url_for('assignChore', ChoreId=ChoreId))
    
    else:
        return render_template("error.html", pageName="createChore", errorName="UnableToCreateChore")

    return True


@app.route('/assignChore', methods=['POST', 'GET'])
def assignChore():
    if request.args.get('ChoreId'):
        ChoreId = request.args.get('ChoreId')
        # get some details of the chore
        chore_details = json.loads(utils.get_chore_details(ChoreId=ChoreId).T.to_json())

        # get a list of people who can do it
        people = json.loads(utils.get_people().T.to_json())
        # print("\n".join([str(v) for v in [ChoreId, chore_details, people]]))
        return render_template("assignChore.html", title="Assign new chore", chore_details=chore_details, people=people)
    else:
        return render_template("error.html", pageName="assignChore", errorName="NoChoreIdSet")


@app.route('/assignChoreAction', methods=['POST', 'GET'])
def assignChoreAction():
    result = request.form
    json_result = dict(result)
    print("assignChoreAction:", json_result)

    ChoreId = int(json_result['ChoreId'])
    del(json_result['ChoreId'])
    for k in json_result:
        print(int(k))
        if not utils.set_responsibility(
            ChoreID=ChoreId,
            PersonID=int(k)
        ):
            return render_template("error.html", pageName="assignChore", errorName=f"Couldn't assign chore {ChoreId} to PersonId {k}")
    utils.update_choreinstances()
    return redirect(url_for('index', title="Chore assigned"))


if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")