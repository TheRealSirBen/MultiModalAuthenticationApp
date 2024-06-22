import streamlit as st
from streamlit import session_state

from cv2 import VideoCapture
from cv2 import flip
from cv2 import cvtColor
from cv2 import COLOR_BGR2RGB

from bson.objectid import ObjectId
from PIL import Image
import csv
import copy
import time
import mediapipe as mp
from os import environ
from yoloface import face_analysis
from numpy import mean
from logging import info

from models.liveness import KeyPointClassifier

from helper import save_user_file, get_finger_index
from helper import convert_and_resize
from helper import pick_random_item
from helper import calc_bounding_rect
from helper import calc_landmark_list
from helper import pre_process_landmark
from helper import draw_landmarks
from helper import draw_expectation
from helper import draw_bounding_rect
from helper import process_upload_fingerprint_file
from helper import FINGER_COLLECTION

from database import insert_record
from database import get_records
from database import delete_records

from datagrip import face_comparison_on_images, delete_image, fingerprint_recognition_on_images

st.set_page_config(
    page_title="Multi Modal Authentication Demo App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # User public id
if 'user_public_id' not in session_state:
    session_state['user_public_id'] = str()

# # User public id
if 'user_name' not in session_state:
    session_state['user_name'] = str()

# # Generate navigation id
if 'navigation_id' not in session_state:
    session_state['navigation_id'] = 0

# # Finger index
if 'finger_index' not in session_state:
    session_state['finger_index'] = 0

if 'finger_check_fail' not in session_state:
    session_state['finger_check_fail'] = 0

# # Camera state
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
    user_public_id_list: list[dict] = get_records('users', login_data, ['_id', 'name'])

    if not user_public_id_list:
        session_state['warning_message'] = 'Email or Password is incorrect!'

    # When user exists
    if user_public_id_list:
        user_public_id_odj = user_public_id_list[0]
        _user_public_id = str(user_public_id_odj.get('_id'))
        _user_name = user_public_id_odj.get('name')
        session_state['user_public_id'] = _user_public_id
        session_state['user_name'] = _user_name
        session_state['navigation_id'] = 1
        session_state['camera_state'] = 1

        session_state['success_message'] = 'Logged in successfully!'

        # Get Past login faces
        logged_in_faces_query_filter = {
            'cloud_file_name': {'$regex': '^{}/'.format(environ.get('LOGIN_FACE_FOLDER'))},
            'user_public_id': _user_public_id
        }
        logged_in_faces_image_paths = get_records(
            'file_path', logged_in_faces_query_filter, ['_id', 'path_id']
        )

        # Delete Past login faces
        for logged_in_face_path_obj in logged_in_faces_image_paths:
            logged_in_face_path = logged_in_face_path_obj.get('path_id')
            delete_logged_in_face_status, delete_logged_in_face_response = delete_image(logged_in_face_path)

            if delete_logged_in_face_status in (200, 404):
                logged_in_face_id = logged_in_face_path_obj.get('_id')
                logged_in_face_id_delete_query = {'_id': logged_in_face_id}
                delete_records('file_path', logged_in_face_id_delete_query)

        # Get Past login fingerprint
        logged_in_fingerprints_query_filter = {
            'cloud_file_name': {'$regex': '^{}/'.format(environ.get('LOGIN_FINGERPRINT_FOLDER'))},
            'user_public_id': _user_public_id
        }
        logged_in_fingerprints_image_paths = get_records(
            'file_path', logged_in_fingerprints_query_filter, ['_id', 'path_id']
        )

        # Delete Past login fingerprint
        for logged_in_fingerprint_path_obj in logged_in_fingerprints_image_paths:
            logged_in_fingerprint_path = logged_in_fingerprint_path_obj.get('path_id')
            delete_logged_in_fingerprint_status, delete_logged_in_fingerprint_response = delete_image(
                logged_in_fingerprint_path
            )

            if delete_logged_in_fingerprint_status in (200, 404):
                logged_in_fingerprint_id = logged_in_fingerprint_path_obj.get('_id')
                logged_in_face_id_delete_query = {'_id': logged_in_fingerprint_id}
                delete_records('file_path', logged_in_face_id_delete_query)


def refresh_login_page(step: str):
    # When performing liveness detection
    if step == 'liveness':
        session_state['navigation_id'] = 2
        st.rerun()

    # When performing facial recognition
    if step == 'recognition':
        session_state['navigation_id'] = 3


def upload_fingerprint_image_clicked():
    _user_public_id = session_state.get('user_public_id')
    path_id, record_id, file_path_check_query = process_upload_fingerprint_file(
        uploaded_fingerprint, _user_public_id, session_finger_index, 'LOGIN_FINGERPRINT_FOLDER'
    )
    fr_status, fr_response = fingerprint_recognition_on_images(path_id, finger_image_path_id)
    message = fr_response.get('message')

    if fr_status == 200:
        session_state['success_message'] = message
        session_state['finger_index'] += 1
        finger_check_fail = session_state['finger_check_fail']
        session_state['finger_check_fail'] = max(0, finger_check_fail - 1)
        session_state.pop('random_finger_index')

        fingerprint_threshold = environ.get('FINGERPRINT_CHECKS')
        if session_state.get('finger_index') >= int(fingerprint_threshold):
            session_state['navigation_id'] = 4

    if fr_status != 200:
        delete_uploaded_fingerprint_status, _ = delete_image(path_id)

        if delete_uploaded_fingerprint_status == 200:
            uploaded_fingerprint_delete_query = {'_id': ObjectId(record_id)}
            delete_records('file_path', uploaded_fingerprint_delete_query)

        session_state['finger_check_fail'] += 1
        session_state['warning_message'] = message

        if session_state.get('finger_check_fail') >= 2:
            logout_button_clicked()
            session_state['warning_message'] = ("You've reached the number fingerprint authentication fails. "
                                                "Please try again.")


def logout_button_clicked():
    session_keys = session_state.keys()

    # Clear session states
    for key in session_keys:
        session_state.pop(key)


st.header("Login", divider='rainbow')

if session_state.get('navigation_id') == 0:
    st.subheader("Password Authentication")
    email_address = st.text_input("Enter your email address:", placeholder="Type your email address here ... ")
    password = st.text_input("Enter your password:", type="password", placeholder="Type your password here ... ")
    st.button("Login", on_click=login_button_clicked)

if session_state.get('navigation_id') == 1:

    st.subheader("Liveness detection check")
    frame_holder = st.empty()

    #
    use_brect = True

    #
    possible_requests = [
        ('right', 'open'), ('right', 'close'), ('right', 'ok'), ('right', 'pointer'), ('left', 'open'),
        ('left', 'close'), ('left', 'pointer')
    ]
    expected_gesture = None

    # Camera preparation #####################################################
    cap = VideoCapture(0)

    # Model load #############################################################
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode='store_true',
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    keypoint_classifier = KeyPointClassifier()

    # Read labels ###########################################################
    with open('models/liveness/keypoint_classifier/keypoint_classifier_label.csv', encoding='utf-8-sig') as f:
        keypoint_classifier_labels = csv.reader(f)
        keypoint_classifier_labels = [
            row[0] for row in keypoint_classifier_labels
        ]

    #  ########################################################################
    user_public_id = session_state.get('user_public_id')
    saved_image_paths: list[dict] = list()
    gesture_index: int = -1
    gesture_count = 0
    liveness_check: list = list()
    liveness_check_threshold = environ.get('LIVENESS_CHECKS')
    face = face_analysis()

    #
    while cap.isOpened():

        #
        if expected_gesture is None and len(liveness_check) < int(liveness_check_threshold):
            random_gesture, gesture_index = pick_random_item(possible_requests)
            _hand, _gesture = random_gesture
            expected_gesture = '{} {}'.format(_hand, _gesture)
            expected_gesture = expected_gesture.lower()
            gesture_count += 1

        # Camera capture ##############################################
        ret, image = cap.read()
        if not ret:
            break

        image = flip(image, 1)  # Mirror display
        image = cvtColor(image, COLOR_BGR2RGB)
        debug_image = copy.deepcopy(image)
        debug_image = draw_expectation(debug_image, expected_gesture, liveness_check)

        # Detection implementation #############################################################
        debug_image.flags.writeable = False
        results = hands.process(debug_image)
        debug_image.flags.writeable = True

        # Loading the face detection model
        _, box, conf = face.face_detection(frame_arr=debug_image, frame_status=True, model='tiny')
        debug_image = face.show_output(debug_image, box, frame_status=True)

        if results.multi_hand_landmarks is not None:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Bounding box calculation
                brect = calc_bounding_rect(debug_image, hand_landmarks)

                # Landmark calculation
                landmark_list = calc_landmark_list(debug_image, hand_landmarks)

                # Conversion to relative coordinates / normalized coordinates
                pre_processed_landmark_list = pre_process_landmark(landmark_list)

                # Hand sign classification
                hand_sign_id = keypoint_classifier(pre_processed_landmark_list)

                # Finger gesture classification
                finger_gesture_id = 0

                # Class label
                hand_class = handedness.classification[0].label[0:]
                keypoint_class = keypoint_classifier_labels[hand_sign_id]
                _class_label = '{} {}'.format(hand_class, keypoint_class)
                class_label = _class_label.lower()

                # Drawing part
                debug_image = draw_bounding_rect(use_brect, debug_image, brect)
                debug_image = draw_landmarks(debug_image, landmark_list)

                if conf:
                    if (class_label == expected_gesture) and conf[0] > 0.7 and box:
                        gesture_check = '{} detected'.format(expected_gesture)
                        liveness_check.append(gesture_check)
                        possible_requests.pop(gesture_index)
                        expected_gesture = None

                        # Save image
                        captured_image = Image.fromarray(image)
                        file_name, image_path = convert_and_resize(
                            captured_image, user_public_id, str(gesture_count), 'LOGIN_FACE_FOLDER'
                        )
                        saved_image_paths.append({'file_name': file_name, 'image_path': image_path})

        # Screen reflection #############################################################
        frame_holder.image(debug_image)

        if len(liveness_check) >= int(liveness_check_threshold):
            time.sleep(1)
            break

    # Release the video capture and writer objects
    cap.release()

    #
    # Get environment variables
    login_image_dir = environ.get('LOGIN_FACE_FOLDER')

    # Save images
    for _image_path_details in saved_image_paths:
        _file_name, _image_path = _image_path_details.get('file_name'), _image_path_details.get('image_path')
        saved_path_id, saved_record_id, saved_file_path_check_query = save_user_file(
            login_image_dir, _file_name, _image_path, user_public_id
        )
    refresh_login_page('liveness')

if session_state.get('navigation_id') == 2:
    st.subheader('Facial Recognition Authentication')

    # Get user
    user_public_id = session_state.get('user_public_id')
    reg_faces_query_filter = {'cloud_file_name': {'$regex': '^faces/'}, 'user_public_id': user_public_id}
    reg_face_images_list = get_records('file_path', reg_faces_query_filter, ['path_id'])

    login_faces_query_filter = {
        'cloud_file_name': {'$regex': '^{}/'.format(environ.get('LOGIN_FACE_FOLDER'))},
        'user_public_id': user_public_id
    }
    login_face_images_list = get_records('file_path', login_faces_query_filter, ['path_id'])

    # Facial Recognition
    if reg_face_images_list and login_face_images_list:

        #
        progress_text = "Running Facial Recognition model. Please wait."
        facial_recognition_progress_bar = st.progress(0, text=progress_text)

        # Iterate over source images
        images_combination_iteration = 0
        number_of_iterations = len(reg_face_images_list) * len(login_face_images_list)
        similarity_matrix: list = list()
        for saved_image_id_path_data in reg_face_images_list:
            saved_image_id_path = saved_image_id_path_data.get('path_id')

            # Iterate over target images
            saved_image_confidence_list: list = list()
            for _image_path_data in login_face_images_list:

                _image_path = _image_path_data.get('path_id')
                comparison_status, comparison_response = face_comparison_on_images(saved_image_id_path, _image_path)

                # When face has been detected
                if comparison_status == 200:
                    face_match_data: dict[dict] = comparison_response.get('data')
                    face_match_details_list: list[dict] = face_match_data.get('FaceMatches')
                    face_match_details: dict = face_match_details_list[0]
                    similarity = face_match_details.get('Similarity')

                    face_comparison_data = {
                        'user_public_id': user_public_id, 'face_data': face_match_data, 'path_id': _image_path
                    }
                    insert_record('face_comparisons', face_comparison_data)

                    saved_image_confidence_list.append(similarity)

                percentage_completion = (images_combination_iteration + 1) / number_of_iterations
                facial_recognition_progress_bar.progress(percentage_completion, text=progress_text)
                images_combination_iteration += 1

            saved_image_average_confidence: float = mean(saved_image_confidence_list)
            similarity_matrix.append(saved_image_average_confidence)

        facial_recognition_progress_bar.empty()

        # Similarity test results
        if similarity_matrix:
            fr_min_confidence = environ.get('FACIAL_RECOGNITION_MIN_CONFIDENCE')
            number_of_saved_images = len(reg_face_images_list)
            saved_images_check = len(
                [confidence for confidence in similarity_matrix if confidence > float(fr_min_confidence)]
            )
            fr_auth_test = saved_images_check / number_of_saved_images
            st.write(
                'We have performed Facial recognition on the liveness detection input. {} out of the {} images '
                'saved at registration matched with at least 99% similarity.'.format(
                    saved_images_check, number_of_saved_images
                )
            )

            # If Facial recognition is successful
            if fr_auth_test > 0.66:
                st.button(
                    'Proceed to Fingerprint Recognition', on_click=refresh_login_page, args=('recognition',)
                )

            else:
                session_state['navigation_id'] = 0
                st.rerun()

if session_state.get('navigation_id') == 3:
    st.subheader('Fingerprint Recognition Authentication')

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
        if registration_type == 'Upload Images':

            stored_image_types = environ.get('IMAGE_TYPES')
            image_types = stored_image_types.split('-')
            finger_index_list = [index for index in FINGER_COLLECTION]

            # Get random finger
            if not session_state.get('random_finger_index'):
                random_finger_index, random_finger_idx = pick_random_item(finger_index_list)
                session_state['random_finger_index'] = random_finger_index

            # Get random finger details
            random_finger = FINGER_COLLECTION.get(session_state.get('random_finger_index'))
            finger_index = get_finger_index(random_finger)
            user_public_id = session_state.get('user_public_id')
            finger_query_filter = {
                'cloud_file_name': 'fingerprints/{}_fr_{}.png'.format(user_public_id, finger_index)
            }
            finger_images_list = get_records('file_path', finger_query_filter, ['path_id'])
            finger_image_path_id_obj = finger_images_list[0]
            finger_image_path_id = finger_image_path_id_obj.get('path_id')

            session_finger_index = session_state.get('finger_index')
            st.write('Upload Image of your {}'.format(random_finger))

            uploaded_fingerprint = st.file_uploader("Choose a file", type=image_types)

            #
            if uploaded_fingerprint is not None:
                st.button('Upload Fingerprint image', on_click=upload_fingerprint_image_clicked)

if session_state.get('navigation_id') == 4:
    st.subheader("Welcome to your online bank account {}".format(session_state.get('user_name')))
    st.button('Logout', on_click=logout_button_clicked)
