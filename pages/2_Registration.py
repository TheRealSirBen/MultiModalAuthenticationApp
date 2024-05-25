import streamlit as st
from streamlit import session_state

from database import insert_record

from datagrip import upload_file_to_aws_s3
from datagrip import detect_face_on_image

from helper import convert_and_resize

from PIL import Image
import cv2
from os import environ
from os.path import exists
from logging import info

st.set_page_config(
    page_title="Multi Modal Authentication Demo App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # Generate navigation id
if 'user_public_id' not in session_state:
    session_state['user_public_id'] = str()

# # Generate navigation id
if 'navigation_id' not in session_state:
    session_state['navigation_id'] = 0

# # Finger index
if 'finger_index' not in session_state:
    session_state['finger_index'] = 0

# # Generate alert state
if (('info_message' not in session_state)
        or ('warning_message' not in session_state)
        or ('success_message' not in session_state)):
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


# #
def save_user_file(file_dir: str, file_name: str, image_path: str, user_public_id: str):
    # Upload image to cloud
    cloud_file_name = '{}/{}'.format(file_dir, file_name)
    aws_s3_upload_status, aws_s3_upload_response = upload_file_to_aws_s3(image_path, cloud_file_name)

    # When upload was successful
    if aws_s3_upload_status == 201:
        # Save s3 file path data
        path_id = aws_s3_upload_response.get('data')
        file_path_data = {
            'file_name': file_name,
            'cloud_file_name': cloud_file_name,
            'path_id': path_id,
            'user_public_id': user_public_id
        }
        file_path_check_query = {'path_id': path_id}
        record_id = insert_record('file_path', file_path_data, check_query=file_path_check_query)
        return path_id, record_id, file_path_check_query


def application_form_button_clicked():
    # Gather data
    application_form_data = {
        'name': form_name,
        'email': form_email_address,
        'password': form_password
    }

    check_filter_data = {'email': form_email_address}

    # Save user data in DB
    user_public_id = insert_record('users', application_form_data, check_query=check_filter_data)

    # When email already exists in db
    if not user_public_id:
        # Alert
        session_state['warning_message'] = 'User with email {} already exists'.format(form_email_address)

    # When new record is inserted
    if user_public_id:
        info('Application form data saved')

        session_state['user_public_id'] = user_public_id
        session_state['navigation_id'] = 1
        session_state['camera_state'] = 1
        session_state['face_image'] = 0

        # Alert
        session_state['success_message'] = 'Application form data submitted and saved!'


def capture_button_clicked():
    session_state['face_image'] += 1
    face_image = session_state.get('face_image')
    user_public_id = session_state.get('user_public_id')
    file_name, image_path = convert_and_resize(captured_image, user_public_id, face_image)

    # Get environment variables
    face_dir = environ.get('FACE_DIR')

    # Save image
    saved_path_id, saved_record_id, saved_file_path_check_query = save_user_file(
        face_dir, file_name, image_path, user_public_id
    )

    # When image is saved
    if saved_path_id:

        # Run face detection
        face_detection_status, face_detection_response = detect_face_on_image(saved_path_id)

        # When success criterion has not been met
        if face_detection_status != 200:
            session_state['face_image'] -= 1

        # When one face has been detected
        if face_detection_status == 200:
            session_state['face_image'] -= 1

            #
            user_public_id = session_state.get('user_public_id')
            face_data = face_detection_response.get('data')
            face_data_record = {'user_public_id': user_public_id, 'face_data': face_data, 'path_id': saved_path_id}
            insert_record('face_detections', face_data_record, check_query=saved_file_path_check_query)

            # Alert
            session_state['success_message'] = 'Face detected in selfie {}.'.format(
                session_state.get('face_image') + 1
            )

            #
            session_state['face_image'] += 1


def process_uploaded_fingerprint():
    # Read the image file
    uploaded_fingerprint_image = Image.open(uploaded_fingerprint)

    # Convert image to png, then resize
    user_public_id = session_state.get('user_public_id')
    fingerprint_file_name, fingerprint_image_path = convert_and_resize(
        uploaded_fingerprint_image, '{}_fr'.format(user_public_id), session_finger_index
    )

    # Get environment variables
    fingerprint_dir = environ.get('FINGERPRINT_DIR')

    # Save file
    save_user_file(fingerprint_dir, fingerprint_file_name, fingerprint_image_path, user_public_id)

    session_state['finger_index'] += 1


def continue_to_fingerprint_button_clicked():
    session_state['navigation_id'] = 2
    session_state['finger_index'] = 1


def submit_image_fingerprints_clicked():
    session_state['navigation_id'] = 3


def new_registration_button_clicked():
    # Reset navigation
    session_state['navigation_id'] = 0


st.header("Registration", divider='rainbow')

# #
# Application form
if session_state.get('navigation_id') == 0:
    #
    st.header('Step 1: Application form')
    form_name = st.text_input('Enter your full name', placeholder='Type your full name here ...')
    form_email_address = st.text_input('Enter your email address', placeholder='Type your email address here ...')
    form_password = st.text_input('Set up your password', type='password', placeholder='Type your password here ...')
    st.button('Submit', on_click=application_form_button_clicked)

# Facial recognition
if session_state.get('navigation_id') == 1:
    sufficient_face_images = environ.get('SUFFICIENT_FACE_IMAGES')
    sufficient_face_images_num = int(sufficient_face_images)

    #
    st.header('Step 2: Register my face')

    # Prepare face capturing
    number_of_selfies = session_state.get('face_image')
    st.subheader(
        ":blue[Selfies for verification ({} out of {} pictures taken)]".format(
            number_of_selfies, sufficient_face_images
        ),
        divider=True,
        help='Up'
    )

    # Camera elements
    frame_holder = st.empty()
    capture_selfie = st.empty()

    # When camera is running
    if session_state.get('camera_state') == 1:

        capture_selfie.button('Take Selfie', on_click=capture_button_clicked)

        cap = cv2.VideoCapture(0, cv2.CAP_GSTREAMER)
        while cap.isOpened():

            ret, frame = cap.read()
            edited_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # When ret is not running
            if not ret:
                break

            # When number of collected images is less than required
            if session_state.get('face_image') < sufficient_face_images_num:
                frame_holder.image(edited_frame)

            # Read the image file
            captured_image = Image.fromarray(edited_frame)

            # When number of collected images is sufficient
            if session_state.get('face_image') >= sufficient_face_images_num:
                info('Sufficient face images captured')
                session_state['camera_state'] = 0
                break
        cap.release()

    # When camera is not running
    if session_state.get('camera_state') == 0:
        frame_holder.empty()
        capture_selfie.empty()
        st.button('Continue to Fingerprint Registrations', on_click=continue_to_fingerprint_button_clicked)

# Fingerprint recognition
if session_state.get('navigation_id') == 2:
    st.header('Step 3: Register my fingerprints')

    navigation, content = st.columns([3, 7])

    with navigation:
        registration_type = st.radio(
            "Select method of submission",
            options=['Upload Images', 'Scan my hands'],
            captions=[
                "I already have images of my scanned fingerprints",
                "I'll scan for my fingerprints using a fingerprint scanner"
            ]
        )

    with content:

        sufficient_fp_images_num = environ.get('SUFFICIENT_FINGERPRINT_IMAGES')
        sufficient_fp_images = int(sufficient_fp_images_num)
        fingerprint_image_size_num = environ.get('FINGERPRINT_IMAGE_SIZE')
        fingerprint_image_size = int(fingerprint_image_size_num)

        if session_state.get('finger_index') >= sufficient_fp_images:
            st.button('Proceed to registration completion', on_click=submit_image_fingerprints_clicked)

        if registration_type == 'Upload Images' and session_state.get('finger_index') < sufficient_fp_images:
            stored_image_types = environ.get('IMAGE_TYPES')
            image_types = stored_image_types.split('-')
            finger_index = {
                1: 'Left little finger',
                2: 'Left ring finger',
                3: 'Left middle finger',
                4: 'Left index finger',
                5: 'Left thumb',
                6: 'Right little finger',
                7: 'Right ring finger',
                8: 'Right middle finger',
                9: 'Right index finger',
                10: 'Right thumb'
            }
            session_finger_index = session_state.get('finger_index')
            st.write('Upload Image of {}'.format(finger_index.get(session_finger_index)))

            uploaded_fingerprint = st.file_uploader("Choose a file", type=image_types)

            if uploaded_fingerprint is not None:
                st.button('Upload Fingerprint image', on_click=process_uploaded_fingerprint)

        # Display collected images
        st.divider()
        st.subheader('Collected Fingerprints')
        fr_1, fr_2, fr_3, fr_4, fr_5 = st.columns([1, 1, 1, 1, 1])
        fr_6, fr_7, fr_8, fr_9, fr_10 = st.columns([1, 1, 1, 1, 1])
        _user_public_id = session_state.get('user_public_id')
        with fr_1:
            fr_1_file = 'images/{}_fr_1.png'.format(_user_public_id)
            if exists(fr_1_file):
                st.image(fr_1_file, width=fingerprint_image_size, caption='Left little finger')
        with fr_2:
            fr_2_file = 'images/{}_fr_2.png'.format(_user_public_id)
            if exists(fr_2_file):
                st.image(fr_2_file, width=fingerprint_image_size, caption='Left ring finger')
        with fr_3:
            fr_3_file = 'images/{}_fr_3.png'.format(_user_public_id)
            if exists(fr_3_file):
                st.image(fr_3_file, width=fingerprint_image_size, caption='Left middle finger')
        with fr_4:
            fr_4_file = 'images/{}_fr_4.png'.format(_user_public_id)
            if exists(fr_4_file):
                st.image(fr_4_file, width=fingerprint_image_size, caption='Left index finger')
        with fr_5:
            fr_5_file = 'images/{}_fr_5.png'.format(_user_public_id)
            if exists(fr_5_file):
                st.image(fr_5_file, width=fingerprint_image_size, caption='Left thumb')
        with fr_6:
            fr_6_file = 'images/{}_fr_6.png'.format(_user_public_id)
            if exists(fr_6_file):
                st.image(fr_6_file, width=fingerprint_image_size, caption='Right little finger')
        with fr_7:
            fr_7_file = 'images/{}_fr_7.png'.format(_user_public_id)
            if exists(fr_7_file):
                st.image(fr_7_file, width=fingerprint_image_size, caption='Right ring finger')
        with fr_8:
            fr_8_file = 'images/{}_fr_8.png'.format(_user_public_id)
            if exists(fr_8_file):
                st.image(fr_8_file, width=fingerprint_image_size, caption='Right middle finger')
        with fr_9:
            fr_9_file = 'images/{}_fr_9.png'.format(_user_public_id)
            if exists(fr_9_file):
                st.image(fr_9_file, width=fingerprint_image_size, caption='Right index finger')
        with fr_10:
            fr_10_file = 'images/{}_fr_10.png'.format(_user_public_id)
            if exists(fr_10_file):
                st.image(fr_10_file, width=fingerprint_image_size, caption='Right thumb')

# Registration complete
if session_state.get('navigation_id') == 3:
    st.header('Registration complete')
    st.write('Proceed to logging in')
    st.divider()
    st.button('New registration', on_click=new_registration_button_clicked)
