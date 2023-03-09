from hashlib import md5
import sqlite3
import pandas as pd
import datetime as dt
import re

class PasswordNotSuppliedError(Exception):
    pass

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

def get_chores(active=False):
    where_str = ''
    if active:
        where_str='where active=True'
    return query_db(q=f"""
        SELECT * FROM chores {where_str}
    """)



def get_chore_details(ChoreId: int = None):
    if ChoreId is None:
        raise NoChoreIdSuppliedError
    
    return query_db(q=f"""
        SELECT * FROM chores where choreid = {ChoreId}
    """)

def get_full_chores_table():
    return query_db(q="""
        SELECT * FROM chores
    """).to_html()

def get_roles():
    return query_db(""" select * from roles """)

roles = get_roles()
role_ids = dict(zip(roles['RoleName'], roles['RoleID']))

def create_person(PersonName: str = None, RoleType: str = None, CurrentBalance: int = 0):
    if not RoleType in role_ids:
        raise UnrecognisedRoleTypeError

    r = update_db(q=f"""
            INSERT INTO people (PersonName, RoleID, CurrentBalance) VALUES ('{PersonName}', {role_ids[RoleType]}, {CurrentBalance});
        """, commit=True)
    return True

def update_balance(
        PersonId: int = None,
        AddBalance: int = 0
    ):
    if PersonId is None:
        raise NoPersonIdSuppliedError
    r=update_db(f"""
        update people set 
            CurrentBalance=CurrentBalance+{AddBalance}
        where
            PersonId={PersonId}
    """)
    return True


def update_person(
        PersonId: int = None,
        PersonName: str = None, 
        RoleId: int = None, 
        CurrentBalance: int = 0
    ):
    if PersonId is None:
        raise NoPersonIdSuppliedError
    print(f"""
    Setting:
        PersonName: {PersonName},
        RoleId: {RoleId},
        CurrentBalance: {CurrentBalance}

    """)
    r=update_db(f"""
        update people set 
            PersonName='{PersonName}', 
            RoleID={RoleId},
            CurrentBalance={CurrentBalance}
        where
            PersonId={PersonId}
    """)
    return True

def get_people():
    return query_db(q="""
        select * from people
    """)

def get_person_details(PersonID: int = None) -> pd.DataFrame:
    if PersonID is None:
        raise NoPersonIdSuppliedError
    
    return query_db(q=f"""
            select 
            personid,
            personName,
            Rolename,
            CurrentBalance,
            sum(iif (validated=1, rate, 0)) as confirmedMoney,
            sum(iif (validated=0, rate, 0)) as pendingMoney
        from 
            people as p 
        left join 
            choreinstances as ci
            on p.PersonId = ci.CompletedBy
        join
            roles as r
        on p.RoleID = r.RoleID

        where 
            personid = {PersonID}
        group by
            personid,
            personName,
            Rolename,
            CurrentBalance
        """)

def check_if_active(row: pd.Series) -> bool:
    retval = False
    test_date = pd.to_datetime(row['start_date']).date()

    # print(row['ChoreID'], test_date)

    if test_date == dt.date.today():
        retval = True

    elif row['repeats']:
        freq, unit = re.findall(r'(\d+)(\w)', row['schedule'])[0]
        if not isinstance(freq, int):
            freq=int(freq)
        # YMWDH
        if unit == 'H':
            # Should change this if we need chores done more
            # often than once a day
            # but code hangs if we use hours=freq
            interval = dt.timedelta(days=1)
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
        
        # TODO: This code doesn't handle time resolutions less than a day
        # Might want to revisit if we need higher frequency than daily 
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
    print(f"Found {len(chore_df)} active chores")
    chore_df['ActiveToday'] = chore_df.apply(check_if_active, axis=1)
    return chore_df[chore_df['ActiveToday'] == True]

def update_chore_rate(ChoreRate: int = 25):
    update_db(f""" 
        INSERT INTO chorerates 
        (Rate, StartDate) 
        VALUES ({ChoreRate}, '{dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d %H:%M:%S")}')
        """)
    return True

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

def get_todays_chores(
    chore_date: dt.datetime = None
    ):
    if chore_date is None:
        chore_date = dt.datetime.now()

    df = query_db(
        f""" select * from choreinstances where date(ChoreDate)=date('{chore_date}')"""
    )
    return df

def update_choreinstances(
    chore_date: dt.datetime = None
):
    if chore_date is None:
        chore_date = dt.datetime.now()

    active_chores = get_active_chores(chore_date.date)

    print("Deleting incomplete chores")
    update_db(f"""
        delete from choreinstances where date(ChoreDate)=date('{chore_date.date()}') and Completed = 0
    """)
    
    print("  ...done.")

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
        print(f"  Processing {ChoreID}")
        if len(query_db(
                f"""
                select * from choreinstances where ChoreID={ChoreID} and ChoreDate='{chore_date.date()}'
                """
            )) == 0:
            update_db(f"""
                INSERT INTO choreinstances 
                (ChoreID, ChoreDate, Completed, Validated, Rate, Banked)
                VALUES 
                ({ChoreID}, '{chore_date.date()}', {completed}, {validated}, {chore_rate}, {banked})
            """)
        else:
            pass
            # print(f"Found {ChoreID} in choreinstances for today")

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
        select * from choreinstances where choreinstanceid={choreInstanceId}
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
    
    update_balance(
        PersonId=chore_check['CompletedBy'].values[0],
        AddBalance=chore_check['Rate'].values[0])

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
        select p.PersonId, p.PersonName, c.choredate, c.ChoreCount 
        from
        people as p
        left join
            (select p.PersonId, PersonName, choredate, count(ChoreInstanceId) as ChoreCount
            from
            people as p
            
            left join
            choreresponsibilities as r
            on r.PersonId = p.PersonId
            
            left join
            choreinstances as i
            on i.ChoreId = r.CHoreId
            where i.ChoreDate='{chore_date}'
            -- and i.Completed=0
            group by PersonName, ChoreDate
            order by PersonName, ChoreDate) as c
        on p.PersonId = c.PersonId
    """).fillna(0)
    chore_df['ChoreCount'] = chore_df['ChoreCount'].astype(int)
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

def get_person_chore_assignment(
        PersonID: int = None
        ) -> pd.DataFrame:
    if PersonID is None:
        raise NoPersonIdSuppliedError
    
    return query_db(q=f"""
        select chores.name, 
            chores.choreid,
            IIF(pc.choreid IS NULL, 1, 0) as assigned
        from chores
        left join
        (SELECT * FROM chores as c
        left join
        choreresponsibilities as cr
        on c.choreid = cr.choreid
        where cr.personid={PersonID}
        
        ) as pc
        on chores.choreid = pc.choreid
        where chores.active=True
    """)

def get_chores_table(
        validated: bool = False,
        completed: bool = True
    ) -> pd.DataFrame:
    
    v,c = 'validated=0', 'completed=0'
    if validated:
        v = 'validated=1' 
    if completed:
        c = 'completed=1'
    where_statement = f'WHERE i.completedBy = p.PersonId AND {" AND ".join([w for w in [v,c] if w])}'
    print (where_statement)
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
        {where_statement}
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

def check_password(password: str = None):
    # need some logic here
    # and to store password in DB?
    if query_db("""select passcode from credentials""")['Passcode'].values[0] == md5(password.encode()).hexdigest():
        return True
    return False

def update_password(password: str = None) -> bool:
    if password is None:
        raise PasswordNotSuppliedError
    
    update_db(q=f""" update credentials
        set Passcode = '{password}'
        where RoldID = '2';
        """,
    commit=True
)