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

# create a boto3 session to s3
session = boto3.Session(
    aws_access_key_id = ACCESS_KEY,
    aws_secret_access_key = SECRET_KEY,
)
s3 = session.resource('s3')

def generate_ticket(data):
    # pdf
    return 0

def upload_ticket_s3(data):
    try:
        s3.meta.client.upload_file(
            Filename=data["ticket_file"], 
            Bucket='speedtrap-tickets',
            Key=f'{data["location"]}/{data["ticket_file"]}')
    except ClientError as e:
        logging.warning(e)
    


def mqtt_publish(data):
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
            client_id = data['location'],
            clean_session = False,
            keep_alive_secs = 10)
    
    # Make the connect() call
    connect_future = mqtt_connection.connect()
    # Future.result() waits until a result is available
    connect_future.result()

    # publish data to IoT Core
    mqtt_connection.publish(topic=data['location'], payload=json.dumps(data), qos=mqtt.QoS.AT_LEAST_ONCE) 
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()

@app.route('/handler', methods=['POST'])
def handler():
    # receive json
    data = request.get_json()

    if 'ticket_file' in data.keys():
        #ticket_file = generate_ticket(data)
        upload_ticket_s3(data)

    mqtt_publish(data)

    return 'OK'


if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5000)