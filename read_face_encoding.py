
# this file will be used to access the face encoding from Firestore Database

import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np

def read_live_database():
    # Initialize Firebase Admin SDK with the service account key
    cred = credentials.Certificate(r'person-counting-6a93a-firebase-adminsdk-gnrt5-432ff74587.json')
    firebase_admin.initialize_app(cred)

    # Access Firestore
    db = firestore.client()
    collection_ref = db.collection('face_encodings')

    # Retrieve all documents in the collection
    docs = collection_ref.stream()

    names = []
    feats = []
    for doc in docs:
        doc = doc.to_dict()
        id = doc['student_id']
        name = doc['name']
        id_name = f'{id}-{name.split()[0]}'    
        
        enc_1 = doc['encoding_center']
        enc_2 = doc['encoding_right']
        enc_3 = doc['encoding_left']
        encs = [enc_1, enc_2, enc_3]
        
        print(id, name, id_name)
        print(enc_1)
        print(enc_2)
        print(enc_3)
        print()   
        
        for enc in encs:
            if enc is not None:
                names.append(name)
                feats.append(enc)
                
        return names, feats

read_live_database()
