import streamlit as st
from streamlit import session_state

from database import insert_record

from datagrip import detect_face_on_image

from helper import process_upload_fingerprint_file
from helper import save_user_file
from helper import convert_and_resize
from helper import FINGER_COLLECTION

from os import environ
from os.path import exists
from os import listdir

from PIL import Image
import cv2
from yoloface import face_analysis
from logging import info

st.set_page_config(
    page_title="Multi Modal Authentication Demo App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # User public id
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


def application_form_button_clicked():
    # Gather data
    application_form_data = {
        'name': form_name,
        'email': form_email_address,
        'password': form_password
    }

    check_filter_data = {'email': form_email_address}

    # Save user data in DB
    _user_public_id = insert_record('users', application_form_data, check_query=check_filter_data)

    # When email already exists in db
    if not _user_public_id:
        # Alert
        session_state['warning_message'] = 'User with email {} already exists'.format(form_email_address)

    # When new record is inserted
    if _user_public_id:
        info('Application form data saved')

        session_state['user_public_id'] = _user_public_id
        session_state['navigation_id'] = 1
        session_state['camera_state'] = 1
        session_state['face_image'] = 0

        # Alert
        session_state['success_message'] = 'Application form data submitted and saved!'


def capture_button_clicked():
    session_state['face_image'] += 1
    face_image = session_state.get('face_image')
    _user_public_id = session_state.get('user_public_id')
    _, _ = convert_and_resize(captured_image, _user_public_id, face_image)

    number_of_faces = len(conf)

    # When no face has been detected
    if number_of_faces == 0:
        session_state['warning_message'] = 'No face detected!'
        session_state['face_image'] -= 1

    # When one face has been detected
    if number_of_faces == 1:
        session_state['face_image'] -= 1

        # Alert
        session_state['success_message'] = 'Face detected in selfie {}.'.format(
            session_state.get('face_image') + 1
        )

        #
        session_state['face_image'] += 1

    # When multiple faces have been detected
    if number_of_faces > 1:
        session_state['face_image'] -= 1
        session_state['warning_message'] = '{} faces were detected.'.format(number_of_faces)


def upload_fingerprint_image_clicked():
    _user_public_id = session_state.get('user_public_id')
    path_id, record_id, file_path_check_query = process_upload_fingerprint_file(
        uploaded_fingerprint, _user_public_id, session_finger_index, 'FINGERPRINT_DIR'
    )

    if record_id:
        session_state['success_message'] = 'Image upload successful'
        session_state['finger_index'] += 1

    if not record_id:
        session_state['warning_message'] = 'Image upload failed. Please re-upload'


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

        cap = cv2.VideoCapture(0)

        face = face_analysis()
        while cap.isOpened():

            ret, frame = cap.read()
            edited_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # When ret is not running
            if not ret:
                break

            # Read the image file
            captured_image = Image.fromarray(edited_frame)

            # When number of collected images is less than required
            if session_state.get('face_image') < sufficient_face_images_num:
                # Loading the face detection models
                _, box, conf = face.face_detection(frame_arr=edited_frame, frame_status=True, model='tiny')
                edited_frame = face.show_output(edited_frame, box, frame_status=True)
                frame_holder.image(edited_frame)

            # When number of collected images is sufficient
            if session_state.get('face_image') >= sufficient_face_images_num:
                info('Sufficient face images captured')
                session_state['camera_state'] = 0
                break

        cap.release()

        #
        image_folder = environ.get('IMAGE_FOLDER')
        all_captured_images = listdir(image_folder)
        user_public_id = session_state.get('user_public_id')
        user_images = [image for image in all_captured_images if image.startswith(user_public_id)]
        number_of_user_images = len(user_images)

        # iterate through all saved images
        progress_text = "Uploading images to cloud storage."
        cloud_storage_upload_progress_bar = st.progress(0, text=progress_text)
        upload_image_iteration = 0
        for file_name in user_images:
            # Get environment variables
            face_dir = environ.get('FACE_DIR')
            image_path = '{}/{}'.format(image_folder, file_name)

            # Save image
            saved_path_id, saved_record_id, saved_file_path_check_query = save_user_file(
                face_dir, file_name, image_path, user_public_id
            )

            # Run face detection
            face_detection_status, face_detection_response = detect_face_on_image(saved_path_id)

            #
            face_data = face_detection_response.get('data')
            face_data_record = {'user_public_id': user_public_id, 'face_data': face_data, 'path_id': saved_path_id}
            insert_record('face_detections', face_data_record, check_query=saved_file_path_check_query)

            percentage_completion = (upload_image_iteration + 1) / number_of_user_images
            cloud_storage_upload_progress_bar.progress(percentage_completion, text=progress_text)
            upload_image_iteration += 1

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

        if registration_type == 'Upload Images' and session_state.get('finger_index') < (sufficient_fp_images + 1):
            stored_image_types = environ.get('IMAGE_TYPES')
            image_types = stored_image_types.split('-')
            finger_index = FINGER_COLLECTION
            session_finger_index = session_state.get('finger_index')
            st.write('Upload Image of {}'.format(finger_index.get(session_finger_index)))

            uploaded_fingerprint = st.file_uploader("Choose a file", type=image_types)

            if uploaded_fingerprint is not None:
                st.button('Upload Fingerprint image', on_click=upload_fingerprint_image_clicked)

        # Display collected images
        st.divider()
        st.subheader('Collected Fingerprints')
        fr_1, fr_2, fr_3, fr_4, fr_5 = st.columns([1, 1, 1, 1, 1])
        fr_6, fr_7, fr_8, fr_9, fr_10 = st.columns([1, 1, 1, 1, 1])
        user_public_id = session_state.get('user_public_id')
        with fr_1:
            fr_1_file = 'images/{}_fr_1.png'.format(user_public_id)
            if exists(fr_1_file):
                st.image(fr_1_file, width=fingerprint_image_size, caption='Left little finger')
        with fr_2:
            fr_2_file = 'images/{}_fr_2.png'.format(user_public_id)
            if exists(fr_2_file):
                st.image(fr_2_file, width=fingerprint_image_size, caption='Left ring finger')
        with fr_3:
            fr_3_file = 'images/{}_fr_3.png'.format(user_public_id)
            if exists(fr_3_file):
                st.image(fr_3_file, width=fingerprint_image_size, caption='Left middle finger')
        with fr_4:
            fr_4_file = 'images/{}_fr_4.png'.format(user_public_id)
            if exists(fr_4_file):
                st.image(fr_4_file, width=fingerprint_image_size, caption='Left index finger')
        with fr_5:
            fr_5_file = 'images/{}_fr_5.png'.format(user_public_id)
            if exists(fr_5_file):
                st.image(fr_5_file, width=fingerprint_image_size, caption='Left thumb')
        with fr_6:
            fr_6_file = 'images/{}_fr_6.png'.format(user_public_id)
            if exists(fr_6_file):
                st.image(fr_6_file, width=fingerprint_image_size, caption='Right little finger')
        with fr_7:
            fr_7_file = 'images/{}_fr_7.png'.format(user_public_id)
            if exists(fr_7_file):
                st.image(fr_7_file, width=fingerprint_image_size, caption='Right ring finger')
        with fr_8:
            fr_8_file = 'images/{}_fr_8.png'.format(user_public_id)
            if exists(fr_8_file):
                st.image(fr_8_file, width=fingerprint_image_size, caption='Right middle finger')
        with fr_9:
            fr_9_file = 'images/{}_fr_9.png'.format(user_public_id)
            if exists(fr_9_file):
                st.image(fr_9_file, width=fingerprint_image_size, caption='Right index finger')
        with fr_10:
            fr_10_file = 'images/{}_fr_10.png'.format(user_public_id)
            if exists(fr_10_file):
                st.image(fr_10_file, width=fingerprint_image_size, caption='Right thumb')

# Registration complete
if session_state.get('navigation_id') == 3:
    st.header('Registration complete')
    st.write('Proceed to logging in')
    st.divider()
    st.button('New registration', on_click=new_registration_button_clicked)
