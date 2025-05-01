import streamlit as st
from firebase import fetch_pending_requests, update_request_status
import time

st.title("Salon Help Requests Dashboard")

st.header("Pending Help Requests")
pending_requests = fetch_pending_requests()

if pending_requests:
    for request_id, request_data in pending_requests.items():
        st.subheader(f"Request ID: {request_id}")
        st.write(f"Question: {request_data['question']}")

        answer = st.text_area(f"Answer for Request ID {request_id}", "")

        if st.button(f"Submit Answer for Request {request_id}"):
            if answer:
                update_request_status(request_id, 'resolved', answer)
                st.success(f"Answer submitted for Request {request_id}")
            else:
                st.error("Please enter an answer before submitting.")

else:
    st.write("No pending help requests.")

st.header("Request History")
history_requests = fetch_pending_requests()

if history_requests:
    for request_id, request_data in history_requests.items():
        st.subheader(f"Request ID: {request_id}")
        st.write(f"Question: {request_data['question']}")
        st.write(f"Status: {request_data['status']}")
        st.write(f"Answer: {request_data['answer'] if request_data.get('answer') else 'Not answered yet'}")
else:
    st.write("No request history available.")
