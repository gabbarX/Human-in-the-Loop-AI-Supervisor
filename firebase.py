import firebase_admin
from firebase_admin import credentials, db


cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://human-in-the-loop-ai-default-rtdb.firebaseio.com'
})

help_requests_ref = db.reference('HelpRequests')

def fetch_pending_requests():
    snapshot = help_requests_ref.order_by_child('status').equal_to('pending').get()
    return snapshot if snapshot else {}

def update_request_status(request_id, status, answer=None):
    help_requests_ref.child(request_id).update({
        'status': status,
        'answer': answer
    })
