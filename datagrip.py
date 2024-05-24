from requests import post
from requests import get
from os import environ
from json import loads
from logging import info

from _init_ import start_app

start_app()

AWS_STORAGE_ENDPOINT = environ.get('AWS_STORAGE_ENDPOINT')
AWS_REKOGNITION_ENDPOINT = environ.get('AWS_REKOGNITION_ENDPOINT')
AWS_BUCKET_NAME = environ.get('APP_NAME')
AWS_REGION_NAME = environ.get('AWS_REGION_NAME')


def create_app_bucket():
    data = {
        "bucket_name": AWS_BUCKET_NAME,
        "region_name": AWS_REGION_NAME
    }
    url = '{}/new'.format(AWS_STORAGE_ENDPOINT)
    data = post(url, json=data)
    status, response = data.status_code, loads(data.text)

    return status, response


def upload_file_to_aws_s3(file_path, file_name):
    data = {
        "bucket_name": AWS_BUCKET_NAME,
        "region_name": AWS_REGION_NAME,
        "file_name": file_name,
        "app_name": AWS_BUCKET_NAME
    }
    files = {"file": open(file_path, "rb")}
    url = '{}/upload'.format(AWS_STORAGE_ENDPOINT)
    data = post(url, files=files, data=data)
    status, response = data.status_code, loads(data.text)

    return status, response


def download_file_from_aws_s3(file_id: str, file_path: str):
    url = '{}/download/{}/{}?region_name={}&app_name={}'.format(
        AWS_STORAGE_ENDPOINT, AWS_BUCKET_NAME, file_id, AWS_REGION_NAME, AWS_BUCKET_NAME
    )
    data = get(url)
    status, content = data.status_code, data.content
    response = str()
    if status == 200:
        with open(file_path, "wb") as file:
            file.write(content)
        file.close()
        response = 'Successfully downloaded'

    return status, response


def detect_face_on_image(image_id: str):
    data = {
        "bucket_name": AWS_BUCKET_NAME,
        "region_name": AWS_REGION_NAME,
        "file_id": image_id,
        "app_name": AWS_BUCKET_NAME
    }
    url = '{}/face-detection-aws-storage'.format(AWS_REKOGNITION_ENDPOINT)
    data = post(url, json=data)
    status, response = data.status_code, loads(data.text)

    return status, response
