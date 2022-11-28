import os
import time
import requests
from datetime import datetime
from uuid import uuid4
from random import randint
from cv2 import VideoCapture, imwrite
from threading import Thread

# helper class for implementing multi-threading
class WebcamStream :
    def __init__(self):
        # create VideoCapture object to access camera
        self.vcap = VideoCapture(0)

        # see if created successfully
        if self.vcap.isOpened() is False :
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)

        self.grabbed , self.frame = self.vcap.read()

        if self.grabbed is False :
            print('[Exiting] No more frames to read')
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
        # grab picture infinitely
        while True :
            if self.stopped is True :
                break

            self.grabbed , self.frame = self.vcap.read()

            if self.grabbed is False :
                print('[Exiting] No more frames to read')
                self.stopped = True
                break
        self.vcap.release()

    def read(self):
        # returns last taken image
        time.sleep(0.5)
        return self.frame

    def stop(self):
        # stops thread
        self.stopped = True


def notify_handler(**kwargs):
    requests.post('http://speedtrap:5000/handler', json=kwargs)


if __name__=='__main__':
    # get speedtrap location and speed_limit
    trap_location = os.environ.get('LOCATION')
    limit = int(os.environ.get('SPEED_LIMIT'))

    # create and start stream in thread
    webcam_stream = WebcamStream()
    webcam_stream.start()

    for _ in range(1000):
        ride_speed = randint(30, 70)
        ride_timestamp = datetime.now().strftime('%H:%M:%S-%d-%m-%Y')

        if ride_speed > limit:
            ticket_pic = webcam_stream.read()
            ride_id = uuid4().hex
            path = f'/tmp/{ride_id}.png'
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

        time.sleep(2)

 
    webcam_stream.stop()