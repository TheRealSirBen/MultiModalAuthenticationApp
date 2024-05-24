from logging import basicConfig
from logging import INFO
from logging import info

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from os import makedirs
from os.path import exists
from os import environ

from requests import post
from json import loads
from sys import stdout
from dotenv import load_dotenv
from uuid import uuid4

basicConfig(stream=stdout, level=INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def create_mongodb_app_db():
    # Unpack Mongodb variables
    mongo_db_uri = environ.get('MONGO_DB_URI')
    mongo_db_password = environ.get('MONGO_DB_PASSWORD')
    uri = mongo_db_uri.replace('<password>', mongo_db_password)
    mongo_db_name = environ.get('APP_NAME')
    mongo_db_test_collection = environ.get('MONGO_DB_TEST_COLLECTION')

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Get the list of database names
    database_names = client.list_database_names()

    # Check if the target database exists
    if mongo_db_name in database_names:
        info('Database {} already exists'.format(mongo_db_name))
        environ['MONGO_DB_EXISTS'] = 'ok'
    else:
        info('Database {} does not exist'.format(mongo_db_name))
        new_database = client[mongo_db_name]
        new_collection = new_database[mongo_db_test_collection]
        new_collection.insert_one({str(uuid4()): str(uuid4())})
        create_mongodb_app_db()

    client.close()


def create_app_bucket():
    aws_bucket_name = environ.get('APP_NAME')
    aws_region_name = environ.get('AWS_REGION_NAME')
    aws_storage_endpoint = environ.get('AWS_STORAGE_ENDPOINT')
    data = {
        "bucket_name": aws_bucket_name,
        "region_name": aws_region_name
    }
    url = '{}/new'.format(aws_storage_endpoint)
    data = post(url, json=data)
    status, response = data.status_code, loads(data.text)
    info(response.get('message'))

    if status == 201:
        environ['AWS_BUCKET_EXISTS'] = 'ok'


def start_app():
    # When environment is dev
    if exists(".dev_env"):
        load_dotenv('.dev_env')
        info('Development environment running')

    # When environment is prod
    else:
        load_dotenv()
        info('Production environment running')

    # Create App dirs
    images_folder = environ.get('IMAGE_FOLDER')
    videos_folder = environ.get('VIDEO_FOLDER')
    temp_dir = environ.get('TEMP_DIR')
    makedirs('logs', exist_ok=True)
    makedirs(images_folder, exist_ok=True)
    makedirs(videos_folder, exist_ok=True)
    makedirs(temp_dir, exist_ok=True)

    # Create Mongodb database
    if 'MONGO_DB_EXISTS' not in environ:
        create_mongodb_app_db()

    # Create Mongodb database
    if 'AWS_BUCKET_EXISTS' not in environ:
        create_app_bucket()
