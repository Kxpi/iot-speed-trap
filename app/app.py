import os
import json
import boto3
import logging
from flask import Flask, request
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
from botocore.exceptions import ClientError


# create the Flask app
app = Flask(__name__)

# get aws credentials from env
ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.environ.get('AWS_SECRET_KEY_ID')
CORE_ENDPOINT = os.environ.get('ENDPOINT')
BUCKET_NAME = os.environ.get('BUCKET_NAME')
TOPIC = os.environ.get('TOPIC')

# create a boto3 session to s3
session = boto3.Session(
    aws_access_key_id = ACCESS_KEY,
    aws_secret_access_key = SECRET_KEY,
)
s3 = session.resource('s3')


def upload_s3(data):
    """
    Uploads picture to S3, returns data with S3 key which will be used to find it in lambda email function
    """
    # create S3 key
    data['s3_key'] = f'{data["location"]}/{data["id"]}.png'

    # upload file to S3
    try:
        s3.meta.client.upload_file(
            Filename = data["ticket_file"], 
            Bucket = BUCKET_NAME,
            Key = data['s3_key'])
    except ClientError as e:
        logging.warning(e)

    return data


def mqtt_publish(data):
    """
    Publishes collected data in form of a JSON to IoT core
    """
    # paths to certificates
    CERTIFICATE = "certificates/certificate.pem.crt"
    PRIVATE_KEY = "certificates/private.pem.key"
    AMAZON_ROOT_CA_1 = "certificates/root.pem"

    # prepare resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint = CORE_ENDPOINT,
            cert_filepath = CERTIFICATE,
            pri_key_filepath = PRIVATE_KEY,
            client_bootstrap = client_bootstrap,
            ca_filepath = AMAZON_ROOT_CA_1,
            client_id = TOPIC,
            clean_session = False,
            keep_alive_secs = 10)
    
    # Make the connect() call
    connect_future = mqtt_connection.connect()
    # Future.result() waits until a result is available
    connect_future.result()

    # publish data to IoT Core
    mqtt_connection.publish(topic=TOPIC, payload=json.dumps(data), qos=mqtt.QoS.AT_LEAST_ONCE) 
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()


@app.route('/handler', methods=['POST'])
def handler():
    # receive json
    data = request.get_json()

    # if the picture was taken, upload to S3
    if 'ticket_file' in data.keys():
        data = upload_s3(data)

    # publish JSON to IoT Core
    mqtt_publish(data)

    return "Published successfully", 201


if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5000)