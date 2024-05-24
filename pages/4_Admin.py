import streamlit as st
from streamlit import session_state
from pandas import DataFrame
from datagrip import download_file_from_aws_s3
from os import environ
from logging import info
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
    faces_query_filter = {'user_public_id': user_public_id}
    face_images_list = get_records('file_path', faces_query_filter, ['path_id', 'file_name'])
    temp_dir = environ.get('TEMP_DIR')
    path_id_key: dict = dict()
    for face_image in face_images_list:
        path_id = face_image.get('path_id')
        file_name = face_image.get('file_name')
        _file_path = '{}/{}'.format(temp_dir, file_name)
        download_file_from_aws_s3(path_id, _file_path)
        path_id_key[path_id] = {'file_path': _file_path, 'file_name': file_name}

    # Draw bounding boxes
    _file_path_list: list = list()
    face_detections_list: list[dict] = get_records(
        'face_detections', faces_query_filter, ['path_id', 'face_data']
    )
    for face_detection in face_detections_list:
        # Read detection data
        face_data: dict = face_detection.get('face_data')
        face_details_list: list[dict] = face_data.get('FaceDetails')
        face_details = face_details_list[0]

        # Read bounding box data
        bounding_box_standardised: dict = face_details.get('BoundingBox')
        detection_path_id = face_detection.get('path_id')
        image_path_details: dict = path_id_key.get(detection_path_id)
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
        _file_path_list.append(display_details)

    return _file_path_list


st.header('Administration Page', divider='rainbow')
required_fields = ['name', 'email']
registered_users = get_records('users', {}, required_fields)
registered_users_df = DataFrame(registered_users)
registered_users_df.columns = [field.capitalize() for field in required_fields]

st.subheader(
    ":blue[Registered Users List]",
    divider=True,
    help='Up'
)
st.dataframe(registered_users_df, use_container_width=True)

registered_users_email_list = registered_users_df['Email'].tolist()
selected_user = st.selectbox('Select user', registered_users_email_list)

if selected_user:
    session_state['selected_user_email'] = selected_user
    file_path_list: list[dict] = get_user_display_data()

    st.subheader(
        ":blue[Captured Images]",
        divider=True,
        help='Up'
    )

    # When files have been downloaded to local dir
    if file_path_list:

        # Iterate over the images
        for file_path in file_path_list:
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
