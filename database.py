from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
from pymongo.server_api import ServerApi
from pymongo.cursor import Cursor

from uuid import uuid4
from os import environ
from logging import info

from _init_ import start_app

#
start_app()

MONGO_DB_URI = environ.get('MONGO_DB_URI')
MONGO_DB_PASSWORD = environ.get('MONGO_DB_PASSWORD')
URI = MONGO_DB_URI.replace('<password>', MONGO_DB_PASSWORD)
MONGO_DB_NAME = environ.get('APP_NAME')


def get_mongo_client() -> MongoClient:
    # Create a new client and connect to the server
    return MongoClient(URI, server_api=ServerApi('1'))


def ping_db() -> str:
    client = get_mongo_client()
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        info("Pinged your deployment. You successfully connected to MongoDB!")
        return 'pong!'
    except Exception as e:
        info(e)
        return 'failed'


def get_collection(collection_name: str) -> tuple[MongoClient, Collection]:
    # Create client
    client = get_mongo_client()
    # Connect to database
    database = client[MONGO_DB_NAME]

    # Collections list
    collections = database.list_collection_names()

    # When collection does not exist
    collection = database[collection_name]
    if collection_name not in collections:
        info('Creating new collection')
        collection = database[collection_name]
        new_record = {str(uuid4()): str(uuid4())}
        collection.insert_one(new_record)
        collection.delete_one(new_record)

    return client, collection


def record_check_by_filter(collection: Collection, filter_query: dict) -> tuple[int, list]:
    records_cursor = collection.find(filter_query)
    records: list = list()
    for record_cursor in records_cursor:
        keys = list(record_cursor.keys())
        record: dict = dict()
        for key in keys:
            record[key] = record_cursor.get(key)

        records.append(record)

    records_count = len(records)
    return records_count, records


def insert_record(collection_name: str, record: dict, check_query: dict = None) -> str:
    # When check query is not provided
    if check_query is None:
        check_query = dict()

    # Get collection
    client, collection = get_collection(collection_name)

    # Check if record exists
    records_count, _ = record_check_by_filter(collection, check_query)

    new_record_id: str = str()
    # When there are no records
    if records_count == 0:
        info("No records")
        # Insert record
        response = collection.insert_one(record)

        client.close()
        new_record_id = str(response.inserted_id)
        return new_record_id

    info('Record already exists')
    return new_record_id


def get_records(collection_name: str, query_filter: dict, keys: list[str]) -> list:
    # Get collection
    client, collection = get_collection(collection_name)

    records_count, all_records = record_check_by_filter(collection, query_filter)
    records: list = list()

    # Iterate over all records
    for row in all_records:
        record: dict = dict()
        # Iterate over all fields
        for key in keys:
            # When key is needed
            if key in row:
                record[key] = row.get(key)

        records.append(record)

    return records
