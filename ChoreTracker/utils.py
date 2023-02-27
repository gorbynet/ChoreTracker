import sqlite3
import pandas as pd
import datetime as dt
import re

class UnrecognisedRoleTypeError(Exception):
    pass

def update_db(
    q: str = None,
    db_name: str = 'ChoreTracker.sqlite3',
    commit: bool = True
    ):
        conn = sqlite3.connect(db_name) 
        cursor = conn.cursor()
        r = cursor.execute(q)
        if commit:
            conn.commit()
        conn.close()
        return r

def query_db(
    q: str = None,
    db_name: str = 'ChoreTracker.sqlite3',
    ):
        conn = sqlite3.connect(db_name) 
        cursor = conn.cursor()
        r = cursor.execute(q).fetchall()
        cols = [c[0] for c in cursor.description]
        conn.close()
        return pd.DataFrame(columns=cols, data=r)

class NoChoreNameSuppliedError(Exception):
    pass

class NoChoreIdSuppliedError(Exception):
    pass

class NoStartDateSuppliedError(Exception):
    pass

class NoStartTimeSuppliedError(Exception):
    pass

class IncorrectTimeWindowFormatError(Exception):
    pass

def create_chore(
    name: str = None,
    schedule: str = '1D',
    start_date: dt.date = dt.date.today(),
    start_time: dt.time = dt.time(7),
    window: str = '4H',
    repeats: bool = True,
    active: bool = True,
):
    if name is None:
        raise NoChoreNameSuppliedError
    if start_date is None:
        start_date = dt.date.today()
        # raise NoStartDateSuppliedError
    if start_time is None:
        start_time = dt.time(7)
        # raise NoStartTimeSuppliedError

    if schedule is None:
        schedule = '1D'

    if window is None:
        window = '4H'

    if repeats is None:
        repeats = False
        
    if active is None:
        active = False

    if not re.match(r'\d+[YWDMH]', schedule):
        raise IncorrectTimeWindowFormatError

    if not re.match(r'\d+[YWDMH]', window):
        raise IncorrectTimeWindowFormatError

    print(f'''name: {name}, schedule: {schedule}, start_date: {start_date}, 
        start_time: {start_time}, window: {window}, REPEATS: {repeats}, active: {active}''')

    update_db(f"""
        INSERT INTO chores 
        (name, schedule, start_date, start_time, window, repeats, active)
        VALUES
        ('{name}', '{schedule}', '{start_date}', '{start_time}', '{window}', {repeats}, {active})
        """)
    
    return True

def delete_chore(choreid:int = None):
    if choreid is None:
        raise NoChoreIdSuppliedError

    update_db(f"""
        delete from chores where ChoreID = {choreid}
    """)
    return True

def get_chores():
    return query_db(q="""
        SELECT * FROM chores
    """)

def get_full_chores_table():
    return query_db(q="""
        SELECT * FROM chores
    """).to_html()

roles = query_db(""" select * from roles """) # .fetchall()
role_ids = dict(zip(roles['RoleName'], roles['RoleID']))

def create_person(PersonName: str = None, RoleType: str = None, CurrentBalance: int = 0):
    if not RoleType in role_ids:
        raise UnrecognisedRoleTypeError

    r = update_db(q=f"""
            INSERT INTO people (PersonName, RoleID, CurrentBalance) VALUES ('{PersonName}', {role_ids[RoleType]}, {CurrentBalance});
        """, commit=True)
    return True

def get_people():
    return query_db(q="""
        select * from people
    """)

def check_if_active(row: pd.Series) -> bool:
    retval = False
    test_date = pd.to_datetime(row['start_date']).date()

    if test_date == dt.date.today():
        retval = True

    elif row['repeats']:
        freq, unit = re.findall(r'(\d+)(\w)', row['schedule'])[0]
        if not isinstance(freq, int):
            freq=int(freq)
        # YMWDH
        if unit == 'H':
            interval = dt.timedelta(hours=freq)
        if unit == 'D':
            interval = dt.timedelta(days=freq)
        if unit == 'W':
            interval = dt.timedelta(days=freq * 7)
        if unit == 'M':
            # TODO:
            # timedelta doesn't do months, need
            # to handle this better
            interval = dt.timedelta(days=freq * 30)
        if unit == 'Y':
            # TODO:
            # What about leap years?
            interval = dt.timedelta(days=freq * 365)
        
        while test_date < dt.date.today():
            test_date += interval
            if test_date == dt.date.today():
                retval = True
                test_date = dt.date.today() + dt.timedelta(days=1)
                break


    return retval

def get_active_chores(
    chore_date: dt.date = None
):
    if chore_date is None:
        chore_date = dt.date.today()
    chore_df = query_db(
        """ SELECT * FROM chores where active = 1 """
    )
    chore_df['ActiveToday'] = chore_df.apply(check_if_active, axis=1)
    return chore_df[chore_df['ActiveToday'] == True]

def update_chore_rate(ChoreRate: int = 25):
    update_db(f""" 
        INSERT INTO chorerates 
        (Rate, StartDate) 
        VALUES ({ChoreRate}, '{dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d %H:%M:%S")}')
        """)

def get_chore_rates():
    return query_db(""" SELECT * FROM chorerates""")

def get_chore_rate(chore_date: dt.datetime = None):
    if chore_date is None:
        chore_date = dt.datetime.now()
    return query_db(f""" 
        select Rate 
        from chorerates 
        join 
            (select max(datetime(StartDate)) as max_date from chorerates where datetime(StartDate) <= datetime('{chore_date}')) as m
        where datetime(StartDate) = m.max_date
        """)['Rate'].values.max()

def update_choreinstances(
    chore_date: dt.datetime = None
):
    if chore_date is None:
        chore_date = dt.datetime.now()
    active_chores = get_active_chores(chore_date.date)
    update_db(f"""
        delete from choreinstances where date(ChoreDate)=date('{chore_date}')
    """)
    chore_rate = get_chore_rate(chore_date)
    # ['ChoreInstanceID',
    #  'ChoreID',
    #  'ChoreDate',
    #  'Completed',
    #  'CompletedBy',
    #  'Validated',
    #  'Rate',
    #  'Banked']
    completed = False
    validated = False
    banked = False
    for ChoreID in active_chores['ChoreID'].values:
        update_db(f"""
            INSERT INTO choreinstances 
            (ChoreID, ChoreDate, Completed, Validated, Rate, Banked)
            VALUES 
            ({ChoreID}, '{chore_date.date()}', {completed}, {validated}, {chore_rate}, {banked})
        """)

class UnrecognisedChoreIDError(Exception):
    pass

class UnrecognisedPersonIDError(Exception):
    pass


def set_responsibility(
    ChoreID: int = None,
    PersonID: int = None,
):
    if not ChoreID in get_chores()['ChoreID'].values:
        raise UnrecognisedChoreIDError
        
    if not PersonID in get_people()['PersonID'].values:
        raise UnrecognisedPersonIDError
        
    update_db(f""" 
        delete from choreresponsibilities 
        where 
        PersonID = {PersonID}
        and
        ChoreID = {ChoreID}
    """)

    update_db(f""" 
        INSERT INTO choreresponsibilities 
        (PersonID, ChoreID) 
        VALUES ({PersonID}, {ChoreID})
    """)

    return True

def get_responsibilities():
    return query_db(""" select * from choreresponsibilities """)

class NoPersonIdSuppliedError(Exception):
    pass

class NoChoreInstanceIdSuppliedError(Exception):
    pass

class ChoreNotCompletedError(Exception):
    pass

class UnrecognisedChoreInstanceIDError(Exception):
    pass

def complete_chore_instance(
    choreInstanceId: int = None,
    personId: int = None,
):
    if personId is None:
        raise NoPersonIdSuppliedError

    if choreInstanceId is None:
        raise NoChoreInstanceIdSuppliedError


    chore_instance_df = query_db(f"""
        select * from choreinstances where choreinstanceid = {choreInstanceId} -- and Completed=0
    """)

    if not len(chore_instance_df) == 1:
        # This is not a valid, incomplete chore
        return False


    person_df = query_db(f""" 
        select r.* from choreresponsibilities as r
        join choreinstances as i
        on r.choreid = i.choreid
        where PersonId = {personId} and i.choreinstanceid = {choreInstanceId}
    """)

    if not len(person_df) == 1:
        # This isn't a valid person/chore combination
        return False
    
    # We've established it's a valid, incomplete chore 
    # and the person is assigned to it, so they're allowed
    # to complete it
    update_db(f"""
        UPDATE choreinstances SET Completed = 1, CompletedBy={personId} where 
        Choreinstanceid = {choreInstanceId}
    """)

    return True

    
def uncomplete_chore_instance(
    choreInstanceId: int = None,
):

    if choreInstanceId is None:
        raise NoChoreInstanceIdSuppliedError

    update_db(f"""
        UPDATE choreinstances SET Completed = 0, Validated=0, Banked=0, CompletedBy=NULL where 
        Choreinstanceid = {choreInstanceId}
    """)

    return True

   
def invalidate_chore_instance(
    choreInstanceId: int = None,
):

    if choreInstanceId is None:
        raise NoChoreInstanceIdSuppliedError

    update_db(f"""
        UPDATE choreinstances SET Validated=0 where 
        Choreinstanceid = {choreInstanceId}
    """)

    return True

def validate_chore_instance(
    choreInstanceId: int = None,
):

    if choreInstanceId is None:
        raise NoChoreInstanceIdSuppliedError

    chore_check = query_db(f"""
        select Completed from choreinstances where choreinstanceid={choreInstanceId}
        """)
    if not len(chore_check) > 0:
        raise UnrecognisedChoreInstanceIDError

    if not chore_check['Completed'].values.max() == 1:
        raise ChoreNotCompletedError

    # Probably need to check it's been done 
    # and validate chore instance id
    
    update_db(f"""
        UPDATE choreinstances SET Validated = 1
        where 
        Choreinstanceid = {choreInstanceId}
    """)

    return True

def bank_owing_amounts(
    personId: int = None, 
    banked_date: dt.date = None
    ):
    # How do we roll this back if it's done by mistake?
    # maybe set a banked date
    if personId is None:
        raise NoPersonIdSuppliedError

    if banked_date is None:
        banked_date = dt.date.today()

    update_db(f"""
        update choreinstances set banked=1, bankeddate='{banked_date}'
        where 
        completedby={personId} and 
        validated = 1 and
        banked = 0
    """)

    return True


def get_chore_counts_by_person(
    chore_date: dt.date = None
):
    if chore_date is None:
        chore_date = dt.date.today()
    chore_df = query_db(f"""
        select p.PersonId, PersonName, choredate, count(ChoreInstanceId) as ChoreCount
        from
        choreinstances as i
        join
        choreresponsibilities as r
        on i.ChoreId = r.CHoreId
        join
        people as p
        on r.PersonId = p.PersonId
        where i.ChoreDate='{chore_date}'
        -- and i.Completed=0
        group by PersonName
        order by PersonName
    """)
    # chore_df = chore_df.T
    # return chore_df.to_json() # 
    # return list(zip(chore_df['PersonID'], chore_df['PersonName'], chore_df['ChoreCount']))
    return chore_df




def get_person_chores(
    personId: int = None,
    chore_date: dt.date = None
):
    if personId is None:
        raise NoPersonIdSuppliedError

    if chore_date is None:
        chore_date = dt.date.today()
    
    print("PersonID:", personId)
    chore_df = query_db(f"""
        select c.name, i.choreinstanceid, i.completed
        from
        choreinstances as i
        join chores as c
        on i.choreid = c.choreid
        join
        choreresponsibilities as r
        on i.ChoreId = r.CHoreId
        join
        people as p
        on r.PersonId = p.PersonId
        where i.ChoreDate='{chore_date}'
        -- and i.completed=0
        and r.PersonId='{personId}'
        -- group by PersonName
        order by PersonName
    """)
    # return list(zip(chore_df['ChoreInstanceID'], chore_df['name'], chore_df['Completed'])) 
    return chore_df

def get_chores_table():
    chore_df = query_db(f"""
        select 
            p.PersonName, 
            i.choreDate, 
            c.name, 
            iif (i.completedBy IS NULL, '', i.completedBy) as CompletedBy,
            i.choreInstanceId, 
            i.completed, 
            i.validated, 
            i.banked
        from
        choreinstances as i
        join chores as c
        on i.choreid = c.choreid
        join
        choreresponsibilities as r
        on i.ChoreId = r.CHoreId
        join
        people as p
        on r.PersonId = p.PersonId
        
        order by choreDate, PersonName
    """)
    return chore_df #.to_html(index=False)

def get_earnings_table():
    chore_df = query_db(f"""
        select 
            p.PersonName, 
            sum(i.completed) as NumberCompleted, 
            sum(i.Rate) as TotalEarned, 
            sum(i.Rate)/100 as PoundsEarned,
            sum(i.validated) as NumberValidated, 
            sum(i.banked) as NumberBanked
        from
        choreinstances as i
        join chores as c
        on i.choreid = c.choreid
        join
        choreresponsibilities as r
        on i.ChoreId = r.CHoreId
        join
        people as p
        on r.PersonId = p.PersonId
        where completed=1
        and completedBy = p.PersonId
        group by PersonName
        order by PersonName
    """)
    return chore_df.to_html(index=False)
