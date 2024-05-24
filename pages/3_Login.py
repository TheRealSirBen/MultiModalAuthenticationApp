import streamlit as st
from streamlit import session_state

import cv2 as cv
from cv2 import VideoCapture
from cv2 import VideoWriter
from cv2 import CascadeClassifier

from os import environ
from helper import frontal_face_detector
from time import sleep
from logging import info

from database import get_records

st.set_page_config(
    page_title="Multi Modal Authentication Demo App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # Generate navigation id
if 'navigation_id' not in session_state:
    session_state['navigation_id'] = 0

# # Generate navigation id
if 'user_public_id' not in session_state:
    session_state['user_public_id'] = str()

# # Generate navigation id
if 'camera_state' not in session_state:
    session_state['camera_state'] = 0

# # Generate alert state
if (('success_message' not in session_state)
        or ('warning_message' not in session_state)
        or ('info_message' not in session_state)):
    #
    session_state['info_message'] = str()
    session_state['warning_message'] = str()
    session_state['success_message'] = str()

# # Alerts
# Info
if session_state.get('info_message'):
    info_message = session_state.get('info_message')
    st.info(info_message)
    session_state['info_message'] = str()

# Warning
if session_state.get('warning_message'):
    info_message = session_state.get('warning_message')
    st.warning(info_message)
    session_state['warning_message'] = str()

# Success
if session_state.get('success_message'):
    info_message = session_state.get('success_message')
    st.success(info_message)
    session_state['success_message'] = str()


def login_button_clicked():
    login_data = {
        'email': email_address,
        'password': password
    }
    info(login_data)
    # user_public_id_list = get_records('users', login_data, ['_id'])
    user_public_id_list = [0]

    if not user_public_id_list:
        session_state['warning_message'] = 'Email or Password is incorrect!'

    # When user exists
    if user_public_id_list:
        user_public_id = user_public_id_list[0]
        session_state['user_public_id'] = user_public_id
        session_state['navigation_id'] = 1
        session_state['camera_state'] = 1

        session_state['success_message'] = 'Logged in successfully!'


def start_recording_button_clicked():
    session_state['camera_state'] = 2


st.header("Login", divider='rainbow')

if session_state['navigation_id'] == 0:
    st.subheader("Password Authentication")
    email_address = st.text_input("Enter your email address:", placeholder="Type your email address here ... ")
    password = st.text_input("Enter your password:", type="password", placeholder="Type your password here ... ")
    st.button("Login", on_click=login_button_clicked)

if session_state['navigation_id'] == 1:

    st.subheader("Facial Recognition Authentication")
    frame_holder = st.empty()
    st.button('Start Recording', on_click=start_recording_button_clicked)

    # Prepare video capturing
    output_dir = environ.get('VIDEO_FOLDER')
    video_duration = environ.get('VIDEO_DURATION')

    cap = VideoCapture(0)
    # Define the codec and create VideoWriter object
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)
    size = (width, height)

    fourcc = cv.VideoWriter_fourcc(*'avc1')
    out = cv.VideoWriter('output.mp4', fourcc, 30.0, size)

    fps = 30  # Specify the frames per second
    number_of_frames = int(video_duration) * fps

    frame_counter = 0
    while cap.isOpened():
        # Loading the required haar-cascade xml classifier file
        classifier_obj = CascadeClassifier('models/haarcascade_frontalface_default.xml')

        ret, frame = cap.read()
        edited_frame = frontal_face_detector(frame, classifier_obj)

        # When ret is not running
        if not ret:
            break

        # When record button has not been clicked
        if session_state.get('camera_state') == 1:
            frame_holder.image(frame)

        # When record button has been clicked and within required video length
        if session_state.get('camera_state') == 2 and frame_counter < (number_of_frames + 1):
            img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            frame_holder.image(img)
            out.write(img)
            frame_counter += 1

        # When record button has been clicked and over required video length
        if session_state.get('camera_state') == 2 and frame_counter >= (number_of_frames + 1):
            break

    # Release the video capture and writer objects
    out.release()
    cap.release()
    session_state['navigation_id'] = 2

if session_state['navigation_id'] == 2:
    st.subheader('FP')
