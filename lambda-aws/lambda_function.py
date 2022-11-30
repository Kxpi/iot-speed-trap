import json
import math
import boto3
from datetime import date
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# max possible 
MAX_TARIFF = {
    'cost': 3000,
    'points': 24
}


def round_up(num):
    """
    Rounds up to closest higher 10 to determine tariff category
    """
    return math.ceil(num / 10) * 10
    
    
def download_pic(event):
    """
    Downloads apropriate picture from S3, return name and path to file
    """
    # create s3 client to download picture to /tmp
    s3 = boto3.client("s3")
    attachment_name = f'{event["id"]}.png'
    save_to = f'/tmp/{attachment_name}'
    try:
        s3.download_file(
        Bucket='speedtrap-tickets', 
        Key=event['s3_key'], 
        Filename=save_to)
    except ClientError as e:
        print(e.response['Error']['Message'])
        
    return attachment_name, save_to
    
    
def lambda_handler(event, context):
    """
    Function responsible for calculating appropriate points and cost for each ticket and sending an email using SES
    """
    # download picture, get name and path of attachment
    attachment_name, attachment_path = download_pic(event)
    
    # calculate over limit diff and choose appropriate punishment from tariff
    over_limit = int(event['speed']) - int(event['speed_limit'])
    tariff_category = str(round_up(over_limit))

    # load json with tariff
    with open('tariff.json') as file:
        tariff = json.load(file)
    
    # pick cost for speeding
    ticket = tariff.get(tariff_category, MAX_TARIFF)
  
    # mail preparation
    message = MIMEMultipart()
    message['Subject'] = f"Title"
    message['From'] = 'sender@mail.com'
    message['To'] = 'receiver@mail.com'
    
    body = f"""
        <p> Message with {ticket['cost']}, {ticket['points']} and other data </p>
    """
    
    part_body = MIMEText(body, 'html')
    message.attach(part_body)
    
    part_attachment = MIMEApplication(open(attachment_path, 'rb').read())
    part_attachment.add_header('Content-Disposition', 'attachment', filename=attachment_name)
    message.attach(part_attachment)
    
    # create client to connect to Amazon SES
    ses_client = boto3.client('ses', region_name = 'us-east-1')
    
    # send e-mail
    try:
        ses_client.send_raw_email(
            Source = message['From'],
            Destinations = [message['To']],
            RawMessage = {'Data': message.as_string()})
  
    except ClientError as e:
        print("Email Delivery Failed! ", e.response['Error']['Message'])
        return 404
    else:
        print("Email successfully sent to " + message['To'] + "!")
        return 200