from cv2 import imread
from cv2 import imwrite
from cv2 import rectangle
from cv2 import cvtColor
from cv2 import COLOR_BGR2GRAY
from cv2 import CascadeClassifier

from os import environ
from random import randint
from PIL import Image
from numpy import array as np_array
from pathlib import Path
import tomli_w


def convert_and_resize(image: Image, filename_key: str, instance_id: str) -> (str, str):
    image_max_size = environ.get('IMAGE_MAX_SIZE')
    image_folder = environ.get('IMAGE_FOLDER')
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

    print(f"Converted .env file to {toml_file}")
