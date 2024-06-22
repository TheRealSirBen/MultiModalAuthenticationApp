import streamlit as st
from streamlit import session_state
from pandas import DataFrame
from datagrip import download_file_from_aws_s3
from os import environ
from os.path import exists
from database import get_records
from helper import format_bounding_box
from helper import draw_bounding_box_on_image
from helper import get_face_details_matrix

st.set_page_config(
    page_title="Multi Modal Authentication Demo App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_user_display_data():
    # Get user_public_id
    user_query_filter = {'email': selected_user}
    user_public_id_list = get_records('users', user_query_filter, ['_id'])
    user_public_id_obj: dict = user_public_id_list[0]
    user_public_id = str(user_public_id_obj.get('_id'))

    # Download images
    faces_query_filter = {'cloud_file_name': {'$regex': '^faces/'}, 'user_public_id': user_public_id}
    fingerprints_query_filter = {'cloud_file_name': {'$regex': '^fingerprints/'}, 'user_public_id': user_public_id}

    face_images_list = get_records('file_path', faces_query_filter, ['path_id', 'file_name'])
    fingerprint_images_list = get_records('file_path', fingerprints_query_filter, ['path_id', 'file_name'])

    temp_dir = environ.get('TEMP_DIR')

    # Faces
    faces_path_id_key: dict = dict()
    for face_image in face_images_list:
        face_path_id = face_image.get('path_id')
        face_file_name = face_image.get('file_name')
        _face_file_path = '{}/face_{}'.format(temp_dir, face_file_name)
        _, _ = download_file_from_aws_s3(face_path_id, _face_file_path)
        faces_path_id_key[face_path_id] = {
            'file_path': _face_file_path, 'file_name': face_file_name
        }

    # Fingerprints
    _fingerprint_file_path_list: list = list()
    for fingerprint_image in fingerprint_images_list:
        fingerprint_path_id = fingerprint_image.get('path_id')
        fingerprint_file_name = fingerprint_image.get('file_name')
        _fingerprint_file_path = '{}/fingerprint_{}'.format(temp_dir, fingerprint_file_name)
        _, _ = download_file_from_aws_s3(fingerprint_path_id, _fingerprint_file_path)
        _fingerprint_file_path_list.append(_fingerprint_file_path)

    # Draw bounding boxes
    _faces_file_path_list: list = list()
    faces_detection_query_filter = {'user_public_id': user_public_id}
    face_detections_list: list[dict] = get_records(
        'face_detections', faces_detection_query_filter, ['path_id', 'face_data']
    )
    for face_detection in face_detections_list:
        # Read detection data
        face_data: dict = face_detection.get('face_data')
        face_details_list: list[dict] = face_data.get('FaceDetails')
        face_details = face_details_list[0]

        # Read bounding box data
        bounding_box_standardised: dict = face_details.get('BoundingBox')
        detection_path_id = face_detection.get('path_id')
        image_path_details: dict = faces_path_id_key.get(detection_path_id)
        image_path = image_path_details.get('file_path')
        image_name = image_path_details.get('file_name')
        bounding_box = format_bounding_box(image_path, bounding_box_standardised)

        # Draw on image
        edited_image_file_path = draw_bounding_box_on_image(image_path, image_name, bounding_box)

        # Prepare face detection matrix
        face_details_matrix = get_face_details_matrix(face_details)

        # Prepare display
        display_details = {
            'original_image_path': image_path,
            'edited_image_file_path': edited_image_file_path,
            'face_detection_matrix': face_details_matrix
        }
        _faces_file_path_list.append(display_details)

    return _faces_file_path_list, _fingerprint_file_path_list


st.header('Administration Page', divider='rainbow')
required_fields = ['name', 'email']
registered_users = get_records('users', {}, required_fields)
registered_users_df = DataFrame(registered_users)

st.subheader(
    ":blue[Registered Users List]",
    divider=True,
    help='Up'
)

if not registered_users_df.empty:
    registered_users_df.columns = [field.capitalize() for field in required_fields]
    st.dataframe(registered_users_df, use_container_width=True)
    registered_users_email_list = registered_users_df['Email'].tolist()
    registered_users_email_list.insert(0, str())
    selected_user = st.selectbox('Select user', registered_users_email_list)

    if selected_user:
        session_state['selected_user_email'] = selected_user
        faces_file_path_list, fingerprint_file_path_list = get_user_display_data()

        # When face files have been downloaded to local dir
        if faces_file_path_list:
            st.subheader(
                ":blue[Captured Images]",
                divider=True,
                help='Up'
            )

            # Iterate over the images
            for file_path in faces_file_path_list:
                original_image, edited_image, detection_details = st.columns([1, 1, 2])
                with original_image:
                    st.image(file_path.get('original_image_path'))

                with edited_image:
                    st.image(file_path.get('edited_image_file_path'))

                with detection_details:
                    face_detection_matrix = file_path.get('face_detection_matrix')
                    face_detection_details = DataFrame(face_detection_matrix)
                    st.dataframe(face_detection_details, use_container_width=True)

                st.divider()

        # When fingerprint files have been downloaded to local dir
        if fingerprint_file_path_list:

            st.subheader(
                ":blue[Captured Fingerprints]",
                divider=True,
                help='Up'
            )

            fingerprint_image_size_num = environ.get('FINGERPRINT_IMAGE_SIZE')
            fingerprint_image_size = int(fingerprint_image_size_num)
            fr_1, fr_2, fr_3, fr_4, fr_5 = st.columns([1, 1, 1, 1, 1])
            fr_6, fr_7, fr_8, fr_9, fr_10 = st.columns([1, 1, 1, 1, 1])
            with fr_1:
                fr_1_file = fingerprint_file_path_list[1 - 1]
                if exists(fr_1_file):
                    st.image(fr_1_file, width=fingerprint_image_size, caption='Left little finger')
            with fr_2:
                fr_2_file = fingerprint_file_path_list[2 - 1]
                if exists(fr_2_file):
                    st.image(fr_2_file, width=fingerprint_image_size, caption='Left ring finger')
            with fr_3:
                fr_3_file = fingerprint_file_path_list[3 - 1]
                if exists(fr_3_file):
                    st.image(fr_3_file, width=fingerprint_image_size, caption='Left middle finger')
            with fr_4:
                fr_4_file = fingerprint_file_path_list[4 - 1]
                if exists(fr_4_file):
                    st.image(fr_4_file, width=fingerprint_image_size, caption='Left index finger')
            with fr_5:
                fr_5_file = fingerprint_file_path_list[5 - 1]
                if exists(fr_5_file):
                    st.image(fr_5_file, width=fingerprint_image_size, caption='Left thumb')
            with fr_6:
                fr_6_file = fingerprint_file_path_list[6 - 1]
                if exists(fr_6_file):
                    st.image(fr_6_file, width=fingerprint_image_size, caption='Right little finger')
            with fr_7:
                fr_7_file = fingerprint_file_path_list[7 - 1]
                if exists(fr_7_file):
                    st.image(fr_7_file, width=fingerprint_image_size, caption='Right ring finger')
            with fr_8:
                fr_8_file = fingerprint_file_path_list[8 - 1]
                if exists(fr_8_file):
                    st.image(fr_8_file, width=fingerprint_image_size, caption='Right middle finger')
            with fr_9:
                fr_9_file = fingerprint_file_path_list[9 - 1]
                if exists(fr_9_file):
                    st.image(fr_9_file, width=fingerprint_image_size, caption='Right index finger')
            with fr_10:
                fr_10_file = fingerprint_file_path_list[10 - 1]
                if exists(fr_10_file):
                    st.image(fr_10_file, width=fingerprint_image_size, caption='Right thumb')
