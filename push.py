import firebase_admin
from firebase_admin import credentials, db
import datetime

import json

# Load from a JSON file
with open('data.json', 'r') as f:
    data = json.load(f)

# init database
cred = credentials.Certificate(r'person-counting-6a93a-firebase-adminsdk-gnrt5-432ff74587.json')  
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://person-counting-6a93a-default-rtdb.asia-southeast1.firebasedatabase.app/' 
})

date_str = datetime.datetime.now().strftime('%d-%m-%Y')
ref = db.reference(date_str)

person_data_list = [
    data
]

try:
    for index, person_data in enumerate(person_data_list):
        person_key = f'person{index + 1}'

        while ref.child(person_key).get() is not None:
            index += 1
            person_key = f'person{index + 1}'

        attendance_ref = ref.child(person_key)
        attendance_ref.set(person_data)

        print(f'Data written successfully to Realtime Database under key {person_key}.')
except Exception as e:
    print(f'Error writing data to Realtime Database: {e}')

