from requests import post
from requests import get
from requests import delete
from requests.exceptions import ConnectionError as RequestsConnectionError
from os import environ
from json import loads
from logging import info

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


def upload_file_to_aws_s3(file_path, file_name, overwrite):
    data = {
        "bucket_name": AWS_BUCKET_NAME,
        "region_name": AWS_REGION_NAME,
        "file_name": file_name,
        "app_name": AWS_BUCKET_NAME,
        "overwrite": overwrite
    }
    files = {"file": open(file_path, "rb")}
    url = '{}/upload'.format(AWS_STORAGE_ENDPOINT)

    try:
        data = post(url, files=files, data=data)
        status, response = data.status_code, loads(data.text)

        return status, response

    except RequestsConnectionError as e:
        info(e)
        return False


def delete_image(file_name: str):
    url = '{}/delete-file/{}?file_name={}&region_name={}&app_name={}'.format(
        AWS_STORAGE_ENDPOINT, AWS_BUCKET_NAME, file_name, AWS_REGION_NAME, AWS_BUCKET_NAME
    )
    data = delete(url)
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


def face_comparison_on_images(source_file_id: str, target_file_id: str):
    data = {
        "region_name": AWS_REGION_NAME,
        "app_name": AWS_BUCKET_NAME,
        "success_match_file_name": 'face_match/{}_{}.png'.format(source_file_id, target_file_id),
        "source_bucket_name": AWS_BUCKET_NAME,
        "source_file_id": source_file_id,
        "target_bucket_name": AWS_BUCKET_NAME,
        "target_file_id": target_file_id
    }
    url = '{}/face-comparison-aws-storage'.format(AWS_REKOGNITION_ENDPOINT)
    data = post(url, json=data)
    status, response = data.status_code, loads(data.text)

    return status, response


def fingerprint_recognition_on_images(source_file_id: str, target_file_id: str):
    data = {
        "region_name": AWS_REGION_NAME,
        "app_name": AWS_BUCKET_NAME,
        'success_match_file_name': 'fingerprint_match/{}_{}.png'.format(source_file_id, target_file_id),
        "source_bucket_name": AWS_BUCKET_NAME,
        "source_file_id": source_file_id,
        "target_bucket_name": AWS_BUCKET_NAME,
        "target_file_id": target_file_id
    }
    url = '{}/fingerprint-recognition-aws-storage'.format(AWS_REKOGNITION_ENDPOINT)
    data = post(url, json=data)
    status, response = data.status_code, loads(data.text)

    return status, response
