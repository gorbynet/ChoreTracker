import streamlit as st
import requests
import pandas as pd
import json

api_url = 'http://localhost:5000/api/v1/resources/{}'

s = requests.Session()

st.title("Hello!")
r = s.get(api_url.format('get_people')).json()
df = pd.DataFrame(json.loads(r['results']))
st.dataframe(df)

buttons = []
for person, personid in zip(df['PersonName'], df['PersonID']):
    buttons.append(st.button(person))




