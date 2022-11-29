# IoT speed trap

## Functionality
University project for Embedded Systems course. Repository contains code needed to deploy a containerized app, with one container serving as a speed trap, and the other one serves as an API that handles sending pictures to AWS S3 and publishing MQTT messages to AWS Iot Core. Further features were also implemented as shown later, in [AWS](#aws) section.

#### NOTE: If you wish to build images and deploy it yourself, please look at issues encountered regarding the [images](#images).

## Device
Below you can find both hardware and software specification. We used BBB with armv7 architecture as our platform but if you want to run it on Raspberry PI with ARM64, checkout [Docker buildx](#images) and build images neccessary for your platform - they should work just fine.

### Hardware - [Beaglebone Black](https://beagleboard.org/black)
* Processor: AM335x 1GHz ARM® Cortex-A8
* 512MB DDR3 RAM
* 4GB 8-bit eMMC on-board flash storage
* Additional 64GB SD card
* OS: Debian 10
* 2 motion sensors
* Logitech C270 USB camera
    
### Software - services
As you will see in docker-compose file, some .env files are provided. They are not in this repo, since they contain secrets and configuration variables used in containers. They are attached below with variables used for this specific project.

#### Speed trap container (**NOTE**: as of now it's only unidirectional)
* Utilizes a USB camera and 2 motion sensors
* Camera is operated in a seperate thread by OpenCV to ensure smooth and always available picture
* Whenever a car passess through a motion sensor, timestamp of this event is saved
* Having 2 timestamps, one after another, from both sensors and knowing the distance between them, we calculate speed
* This data, along with configured location and last timestamp is **always** sent to API and publishd via MQTT to AWS IoT Core
* If the speed is greater than configured limit, camera takes a picture and saves it into shared volume
* In this case, additional data like path to file and ID of event (which also serves as a file name) are added to JSON sent to API
* .env: \
![image](https://user-images.githubusercontent.com/70852683/204422549-b00697dc-e736-4ac9-9d8f-3a22b2407b1d.png)

    
#### API container
* Works as a service for HTTP and MQTT operations
* If data has a field with path to picture that will be used to generate a ticket, the picture is uploaded to S3
* It **always** publishes received data to AWS IoT Core
* In order for MQTT messages to work, you need to add **certificates** sub-directory in /app. After that, generate and place there neccessary files mentioned in this [instruction](https://aws.amazon.com/premiumsupport/knowledge-center/iot-core-publish-mqtt-messages-python/)
* .env: \
![image](https://user-images.githubusercontent.com/70852683/204422689-36779716-7779-4484-aa08-fccaf440bec9.png)



#### Diagram
<p align="center">
  <img src="https://github.com/Kxpi/iot-speed-trap/blob/main/images/DeviceArchitecture.jpg?raw=true" width=60%/>
</p>

### AWS
AWS IoT Core is a service that allows to add *things* that will publish their data over MQTT. It's possible to subscribe to given topic and lookup incoming data. There were 2 IoT Rules created - one is triggered on every message received, adding records to AWS Timestream DB, and the other rule acts every time there is a field with ticket. The second one invokes a AWS Lambda function responsible for generating a PDF ticket with picture from S3 and sending it via e-mail to (for now) examplary driver. Timestream stores all recorded measurements, which allows to utilize Grafana to analyze and filter collected data.

#### Infrastructure
<p align="center">
  <img src="https://github.com/Kxpi/iot-speed-trap/blob/main/images/IoT_Architecture.png?raw=true" width=60%/>
</p>

## Performance
Due to low resources available, it's highly recommended to build Docker images on a different, stronger machine and pull them on target device. Let's be honest, 512MB RAM isn't much. Choosing Docker Compose over K3s also allowed to minimize CPU and RAM usage with both usually staying way below 50%.

## Images
As mentioned, it's hard to build images on such low-RAM device, and it's easierr to build them on a proper machine and pull from hub on Beaglebone/Raspberry later (if network speed will be tolerable). However, because of different architectures we can't use e.g. AMD64 image. A very helpful tool is **buildx** command which comes standard with most of Docker installations. When building an image, it allows to specify for which platform it's supposed to be. Below is an example of how to build and push an image of camera service:
```
docker buildx create --name builder
docker buildx use builder
docker buildx build --push --platform linux/arm/v7 -t [username]/camera:test ./camera
```
When you will have the images, just channge their names in [docker-compose.yaml](docker-compose.yaml) and you should be good to go.

## Possible issues with OpenCV
When working with OpenCV, we encountered an error/warning almost every time it took a picture (so with 30FPS it was around 30 times every second).
```
Corrupt JPEG data: 2 extraneous bytes before marker 0xd9
```
Number of extraneous bytes was varying between 1 and 4. Although it's a known issue, widely discussed on forums, we didn't find a solution. Technically there was no need because the pictures were completely fine so it could be faulty camera (there were many issues reported with C270 on Linux).
