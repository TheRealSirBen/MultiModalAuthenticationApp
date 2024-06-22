from cv2 import imread
from cv2 import imwrite
from cv2 import rectangle
from cv2 import cvtColor
from cv2 import COLOR_BGR2GRAY
from cv2 import CascadeClassifier
from cv2 import boundingRect
from cv2 import line
from cv2 import circle
from cv2 import putText
from cv2 import FONT_HERSHEY_SIMPLEX
from cv2 import LINE_AA

from os import environ
from random import randint
from PIL import Image
from numpy import array as np_array
from pathlib import Path
import tomli_w
from logging import info

import numpy as np
import random
import copy
import itertools
import csv

from database import insert_record
from datagrip import upload_file_to_aws_s3

FINGER_COLLECTION = {
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


def get_finger_index(finger_name: str) -> int:
    for finger in FINGER_COLLECTION:
        if finger_name == FINGER_COLLECTION[finger]:
            return finger


def save_user_file(file_dir: str, file_name: str, image_path: str, _user_public_id: str, overwrite: bool = False):
    # Upload image to cloud
    cloud_file_name = '{}/{}'.format(file_dir, file_name)
    aws_s3_upload_status, aws_s3_upload_response = upload_file_to_aws_s3(image_path, cloud_file_name, overwrite)

    path_id, record_id, file_path_check_query = str(), str(), dict()

    # When upload was successful
    if aws_s3_upload_status == 201:
        # Save s3 file path data
        path_id = aws_s3_upload_response.get('data')
        file_path_data = {
            'file_name': file_name,
            'cloud_file_name': cloud_file_name,
            'path_id': path_id,
            'user_public_id': _user_public_id
        }
        file_path_check_query = {'path_id': path_id}
        record_id = insert_record('file_path', file_path_data, check_query=file_path_check_query)

    return path_id, record_id, file_path_check_query


def process_upload_fingerprint_file(uploaded_fingerprint, user_public_id, session_finger_index, fingerprint_dir_path):
    # Read the image file
    uploaded_fingerprint_image = Image.open(uploaded_fingerprint)

    # Convert image to png, then resize
    fingerprint_file_name, fingerprint_image_path = convert_and_resize(
        uploaded_fingerprint_image, '{}_fr'.format(user_public_id), session_finger_index
    )

    # Get environment variables
    fingerprint_dir = environ.get(fingerprint_dir_path)

    # Save file
    path_id, record_id, file_path_check_query = save_user_file(
        fingerprint_dir, fingerprint_file_name, fingerprint_image_path, user_public_id
    )

    return path_id, record_id, file_path_check_query


def calc_bounding_rect(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_array = np.empty((0, 2), int)

    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point = [np.array((landmark_x, landmark_y))]

        landmark_array = np.append(landmark_array, landmark_point, axis=0)

    x, y, w, h = boundingRect(landmark_array)

    return [x, y, x + w, y + h]


def calc_landmark_list(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_point = []

    # Keypoint
    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point.append([landmark_x, landmark_y])

    return landmark_point


def pre_process_landmark(landmark_list):
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, landmark_point in enumerate(temp_landmark_list):
        if index == 0:
            base_x, base_y = landmark_point[0], landmark_point[1]

        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

    # Convert to a one-dimensional list
    temp_landmark_list = list(
        itertools.chain.from_iterable(temp_landmark_list))

    # Normalization
    max_value = max(list(map(abs, temp_landmark_list)))

    def normalize_(n):
        return n / max_value

    temp_landmark_list = list(map(normalize_, temp_landmark_list))

    return temp_landmark_list


def pre_process_point_history(image, point_history):
    image_width, image_height = image.shape[1], image.shape[0]

    temp_point_history = copy.deepcopy(point_history)

    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, point in enumerate(temp_point_history):
        if index == 0:
            base_x, base_y = point[0], point[1]

        temp_point_history[index][0] = (temp_point_history[index][0] -
                                        base_x) / image_width
        temp_point_history[index][1] = (temp_point_history[index][1] -
                                        base_y) / image_height

    # Convert to a one-dimensional list
    temp_point_history = list(
        itertools.chain.from_iterable(temp_point_history))

    return temp_point_history


def logging_csv(number, mode, landmark_list, point_history_list):
    if mode == 0:
        pass
    if mode == 1 and (0 <= number <= 9):
        csv_path = 'model/keypoint_classifier/keypoint.csv'
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *landmark_list])
    if mode == 2 and (0 <= number <= 9):
        csv_path = 'model/point_history_classifier/point_history.csv'
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *point_history_list])
    return


def draw_landmarks(image, landmark_point):
    if len(landmark_point) > 0:
        # Thumb
        line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
             (255, 255, 255), 2)

        # Index finger
        line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
             (255, 255, 255), 2)

        # Middle finger
        line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
             (255, 255, 255), 2)

        # Ring finger
        line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
             (255, 255, 255), 2)

        # Little finger
        line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
             (255, 255, 255), 2)

        # Palm
        line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
             (255, 255, 255), 2)
        line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
             (0, 0, 0), 6)
        line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
             (255, 255, 255), 2)

    # Key Points
    for index, landmark in enumerate(landmark_point):
        if index == 0:  # 手首1
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 1:  # 手首2
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 2:  # 親指：付け根
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 3:  # 親指：第1関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 4:  # 親指：指先
            circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 5:  # 人差指：付け根
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 6:  # 人差指：第2関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 7:  # 人差指：第1関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 8:  # 人差指：指先
            circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 9:  # 中指：付け根
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 10:  # 中指：第2関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 11:  # 中指：第1関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 12:  # 中指：指先
            circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 13:  # 薬指：付け根
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 14:  # 薬指：第2関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 15:  # 薬指：第1関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 16:  # 薬指：指先
            circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 17:  # 小指：付け根
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 18:  # 小指：第2関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 19:  # 小指：第1関節
            circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 20:  # 小指：指先
            circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                   -1)
            circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)

    return image


def pick_random_item(items: list):
    """
    Randomly picks an item from the given list of tuples.

    Args:
        items (list): A list of tuples.

    Returns:
        tuple: A randomly selected item from the list.
    """
    if not items:
        return None

    random_item = random.choice(items)
    random_item_index = items.index(random_item)
    return random_item, random_item_index


def draw_expectation(image, expected_gesture, liveness_check: list):
    putText(image, expected_gesture, (50, 30), FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, LINE_AA)
    putText(image, expected_gesture, (50, 30), FONT_HERSHEY_SIMPLEX, 1.0, (255, 10, 10), 2, LINE_AA)
    check = 0
    for text in liveness_check:
        text = text.capitalize()
        y_coordinate = 90 + (check * 50)
        putText(image, text, (50, y_coordinate), FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, LINE_AA)
        putText(image, text, (50, y_coordinate), FONT_HERSHEY_SIMPLEX, 1.0, (10, 255, 10), 2, LINE_AA)
        check += 1

    return image


def select_mode(key, mode):
    number = -1
    if 48 <= key <= 57:  # 0 ~ 9
        number = key - 48
    if key == 110:  # n
        mode = 0
    if key == 107:  # k
        mode = 1
    if key == 104:  # h
        mode = 2
    return number, mode


def draw_info_text(image, brect, handedness, hand_sign_text, finger_gesture_text):
    rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)

    info_text = handedness.classification[0].label[0:]
    if hand_sign_text != "":
        info_text = info_text + ':' + hand_sign_text
    putText(
        image, info_text, (brect[0] + 5, brect[1] - 4),
        FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, LINE_AA
    )

    if finger_gesture_text != "":
        putText(
            image, "Finger Gesture:" + finger_gesture_text, (10, 60),
            FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, LINE_AA
        )
        putText(
            image, "Finger Gesture:" + finger_gesture_text, (10, 60),
            FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2,
            LINE_AA
        )

    return image


def draw_bounding_rect(use_brect, image, brect):
    if use_brect:
        # Outer rectangle
        rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]),
                  (0, 0, 0), 1)

    return image


def draw_point_history(image, point_history):
    for index, point in enumerate(point_history):
        if point[0] != 0 and point[1] != 0:
            circle(image, (point[0], point[1]), 1 + int(index / 2),
                   (152, 251, 152), 2)

    return image


def draw_info(image, fps, mode, number):
    putText(image, "FPS:" + str(fps), (10, 30), FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, LINE_AA)
    putText(image, "FPS:" + str(fps), (10, 30), FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, LINE_AA)

    mode_string = ['Logging Key Point', 'Logging Point History']
    if 1 <= mode <= 2:
        putText(
            image,
            "MODE:" + mode_string[mode - 1],
            (10, 90), FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
            LINE_AA
        )
        if 0 <= number <= 9:
            putText(
                image, "NUM:" + str(number), (10, 110),
                FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                LINE_AA
            )
    return image


def convert_and_resize(image: Image, filename_key: str, instance_id: str, dest_dir: str = 'IMAGE_FOLDER') -> (str, str):
    image_max_size = environ.get('IMAGE_MAX_SIZE')
    image_folder = environ.get(dest_dir)
    image_max_size_input = (int(image_max_size), int(image_max_size))

    # Resize the image while maintaining the aspect ratio
    image.thumbnail(image_max_size_input)

    # Out filename
    output_filename = '{}_{}.png'.format(filename_key, instance_id)
    output_filepath = '{}/{}'.format(image_folder, output_filename)

    # Save the resized image
    image.save(output_filepath)

    return output_filename, output_filepath


def get_image_dimensions(image_path):
    with Image.open(image_path) as image:
        width, height = image.size
        return width, height


def draw_bounding_box_on_image(image_path: str, image_name: str, bounding_box: dict):
    # Load the image
    image = imread(image_path)
    color = (randint(0, 255), randint(0, 255), randint(0, 255))

    # Define the coordinates of the bounding box
    x = bounding_box.get('x')
    y = bounding_box.get('y')
    w = bounding_box.get('w')
    h = bounding_box.get('h')

    # Draw the bounding box on the image
    rectangle(image, (x, y), (x + w, y + h), color, 3)

    # Save the image with the bounding box
    temp_dir = environ.get('TEMP_DIR')
    output_filepath = '{}/detection_{}'.format(temp_dir, image_name)
    imwrite(output_filepath, image)

    return output_filepath


def format_bounding_box(image_path: str, original_bounding_box: dict) -> dict:
    image_width, image_height = get_image_dimensions(image_path)

    # Format bounding box
    bounding_box: dict = dict()
    bounding_box['x'] = int(original_bounding_box.get('Left') * image_width)
    bounding_box['y'] = int(original_bounding_box.get('Top') * image_height)
    bounding_box['w'] = int(original_bounding_box.get('Width') * image_width)
    bounding_box['h'] = int(original_bounding_box.get('Height') * image_height)

    return bounding_box


def get_face_details_matrix(face_details: dict) -> list:
    details_matrix: list = list()
    #
    confidence = face_details.get('Confidence')
    gender: dict = face_details.get('Gender')
    age_range: dict = face_details.get('AgeRange')
    mouth_open: dict = face_details.get('MouthOpen')
    eyes_open: dict = face_details.get('EyesOpen')

    #
    details_matrix.append({'Attribute': 'Face detection', 'Prediction': 'True', '% Confidence': confidence})
    details_matrix.append(
        {'Attribute': 'Gender', 'Prediction': gender.get('Value'), '% Confidence': gender.get('Confidence')}
    )
    details_matrix.append(
        {
            'Attribute': 'Age range',
            'Prediction': 'Between {} to {}'.format(age_range.get('Low'), age_range.get('High')),
            '% Confidence': 99.99
        }
    )
    details_matrix.append(
        {
            'Attribute': 'Mouth open',
            'Prediction': str(mouth_open.get('Value')),
            '% Confidence': mouth_open.get('Confidence')
        }
    )
    details_matrix.append(
        {
            'Attribute': 'Eyes open',
            'Prediction': str(eyes_open.get('Value')),
            '% Confidence': eyes_open.get('Confidence')
        }
    )

    return details_matrix


def frontal_face_detector(image_obj: np_array, classifier_obj: CascadeClassifier) -> np_array:
    # Converting image to grayscale
    gray_img = cvtColor(image_obj, COLOR_BGR2GRAY)

    # Applying the face detection method on the grayscale image
    faces_rect = classifier_obj.detectMultiScale(gray_img, 1.1, 9)

    # Iterating through rectangles of detected faces
    for (x, y, w, h) in faces_rect:
        rectangle(image_obj, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return image_obj


def env_to_toml(filename: str):
    # Set the path to your .env file
    env_file = Path(filename)

    # Read the environment variables from the .env file
    env_vars = {}
    with env_file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key] = value

    # Write the environment variables to a TOML file
    toml_file = Path('config.toml')
    with toml_file.open('wb') as f:
        tomli_w.dump(env_vars, f)

    info("Converted .env file to {}".format(toml_file))


if __name__ == '__main__':
    save_user_file('.env_dev')
