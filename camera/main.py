import os
import time
import logging
import requests
from time import time, sleep
from uuid import uuid4
from threading import Thread
from datetime import datetime
import Adafruit_BBIO.GPIO as GPIO
from cv2 import VideoCapture, imwrite

# setup GPIO with pins that receive signals
START_PIN = os.environ.get('START_PIN')
EXIT_PIN = os.environ.get('EXIT_PIN')
GPIO.setup(START_PIN, GPIO.IN)
GPIO.setup(EXIT_PIN, GPIO.IN)

# use multiplier to get different speed values - default should be 1
MULTIPLIER = int(os.environ.get('MULTIPLIER'))

# this variable specifies delay time before taking frame from Webcam thread (variable with frame is updated with slight delay)
OFFSET = float(os.environ.get('OFFSET'))

# helper class for camera in thread
class WebcamStream :
    def __init__(self):
        # create VideoCapture object to access camera
        self.vcap = VideoCapture(0)

        # see if created successfully
        if self.vcap.isOpened() is False :
            logging.error("[Exiting]: Error accessing webcam stream.")
            exit(0)

        # first read is used for validation purposes
        self.grabbed , self.frame = self.vcap.read()

        if self.grabbed is False :
            logging.error('[Exiting] No more frames to read')
            exit(0)

        # set stopped to true before starting new thread
        self.stopped = True

        # create thread to capture image
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True # daemon threads run in background

    def start(self):
        # start capturing in thread
        self.stopped = False
        self.t.start()

    def update(self):
        # grabs picture infinitely on ~30fps
        while True :
            if self.stopped is True :
                break

            self.grabbed , self.frame = self.vcap.read()

            if self.grabbed is False :
                logging.error('[Exiting] No more frames to read')
                self.stopped = True
                break
        self.vcap.release()

    def read(self):
        # returns last taken image
        sleep(OFFSET)
        return self.frame

    def stop(self):
        # stops thread
        self.stopped = True


def notify_handler(**kwargs):
    # sends a post with measured data (and optionaly path to ticket image) to api service
    requests.post('http://speedtrap-api:5000/handler', json=kwargs)


def measure_speed(distance, timeout):
    """
    Measures speed of cars passing through two proximity sensors
    """
    # setup timeout
    timeout = time() + timeout
    # listen for falling edge on START_PIN
    while True:
        if GPIO.input(START_PIN) == 0:
            start = time()
            # listen for falling edge on exit pin with timeout
            while (time() - start < timeout):
                if GPIO.input(EXIT_PIN) == 0:
                    # calculate and return velocity [km/h]
                    exit = time()
                    time_passed = exit - start
                    v_kmh = (distance / time_passed) * 3.6
                    v = round(v_kmh, 2)
                    return v * MULTIPLIER
            # return -1 if timeout
            else:
                return -1
                


if __name__=='__main__':
    # get speedtrap location, speed_limit, distance and timeout value
    trap_location = os.environ.get('LOCATION')
    limit = int(os.environ.get('SPEED_LIMIT'))
    distance = float(os.environ.get('DISTANCE'))
    timeout = int(os.environ.get('TIMEOUT'))

    # create and start stream in thread
    webcam_stream = WebcamStream()
    webcam_stream.start()

    while(True):
        ride_speed = measure_speed(distance, timeout)
        ride_timestamp = datetime.now().strftime('%H:%M:%S-%d-%m-%Y')

        if ride_speed > 0:
            if ride_speed > limit:
                ticket_pic = webcam_stream.read()
                ride_id = uuid4().hex
                path = f'/opt/{ride_id}.png'
                imwrite(path , ticket_pic)
                notify_handler(
                    id = ride_id,
                    speed = ride_speed,
                    speed_limit = limit,
                    timestamp = ride_timestamp,
                    ticket_file = path,
                    location = trap_location)
            else:
                notify_handler(
                    speed = ride_speed,
                    speed_limit = limit,
                    timestamp = ride_timestamp,
                    location = trap_location)

        else:
            print('Timeout')
