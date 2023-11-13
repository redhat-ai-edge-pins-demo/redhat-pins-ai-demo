# test
import cv2
import base64
import io, os
import numpy as np
from flask_socketio import emit, SocketIO
from flask import Flask, render_template
import sys
import time
import torch
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

# MQTT broker configuration
mqtt_broker = "192.168.10.107"
mqtt_port = 1884
mqtt_topic = "/cam/state"
mqtt_username = "your_username"
mqtt_password = "your_password"
camera_move = False

def on_connect(client, userdata, flags, rc):  
    # The callback for when the client connects to the broker 
    print("Connected with result code {0}".format(str(rc)))  

def on_message(client, userdata, msg):  
    # The callback for when a PUBLISH message is received from the server. 
    print("Message received-> "  + msg.topic + " " + str(msg.payload))
    if msg.topic == "/cam/index" and str(msg.payload) == "next":
        camera_move = True

client = mqtt.Client("orin_frame_reader") 
client.on_connect = on_connect 
client.on_message = on_message 
try:
    client.connect("192.168.10.107", 1884, 60)
    print("MQTT connected", file=sys.stdout)
except:
    print("MQTT Error", file=sys.stdout)

client.loop_forever()

mqclient.subscribe("/cam/index")

external_host = os.environ.get("EXTERNAL_HOST")
external_port = os.environ.get("EXTERNAL_PORT")

model = torch.hub.load('yolov5', 'custom', path='best.pt', source='local')


app = Flask(__name__, template_folder="/app/templates")
app.secret_key = 'Shadowman42'
sio = SocketIO(app)

dim = (640, 640)
dim_show = (1280, 720)

def get_video_frames():
    print("START", file=sys.stdout)

    
    if cv2.VideoCapture(1).isOpened():
        cap = cv2.VideoCapture(1)
    elif cv2.VideoCapture(0).isOpened():
        cap = cv2.VideoCapture(0)
    elif cv2.VideoCapture('video.mp4').isOpened():
        cap = cv2.VideoCapture('video.mp4')
    else:
        print("No video opened", file=sys.stdout)
        sys.exit()

    fps = cap.get(cv2.CAP_PROP_FPS)
    print(fps)
    print(cap.get(cv2.CAP_PROP_FRAME_COUNT), file=sys.stdout)
    frame_counter= 0
    frame_result_counter=0


    while True:
        # Read a frame from the camera
        ret, frame = cap.read()
        frame_counter += 1
        frame_result_counter += 1
        bad_pins=False
        #If the last frame is reached, reset the capture and the frame_counter
        if frame_counter == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            #print("== last frame ==", file=sys.stdout)
            frame_counter = 0 #Or whatever as long as it is the same as next line
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if not ret:
            #print("Error: Could not read a frame.", file=sys.stdout)
            sys.exit

        if camera_move == False:
            resized = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)
            results = model(resized)
            if results.pandas().xyxy[0].empty:
                pass
            else:
                for i in results.pandas().xyxy[0]['name']:
                    print(i, file=sys.stdout)
                    if i == "PaintLeak":
                        bad_pins=True
            
            if frame_counter == 60:
                if bad_pins == True:
                    #send KeyError
                    print("BadPin", file=sys.stdout)
                else:
                    #send ok
                    print("GoodPin", file=sys.stdout)
                frame_counter = 0
                bad_pins = False
                time.sleep(1)
                    
            #results.print()
            results_resized = cv2.resize(np.squeeze(results.render()), dim_show, interpolation = cv2.INTER_AREA)
        else:
            results_resized = frame    
            
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_bytes = cv2.imencode('.jpg', results_resized)[1]
        stringData = base64.b64encode(frame_bytes).decode('utf-8')
        b64_src = 'data:image/jpeg;base64,'
        stringData = b64_src + stringData
        sio.emit('response_back', stringData, namespace="/")

def send_frame_to_mqtt(frame_bytes):
    try:
        # Publish the frame as a message to the MQTT broker
        #auth = {'username': mqtt_username, 'password': mqtt_password}
        publish.single(mqtt_topic, payload=frame_bytes, hostname=mqtt_broker) #, auth=auth
    except Exception as e:
        print(f"Error sending frame to MQTT broker: {e}")

@sio.on('connect')
def connect():
    #print('Connected')
    pass

@sio.on('start-task')
def start_task():
    print('Start background')
    sio.start_background_task(
        generate_frames,
        current_app.get_current_object()
        )

@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    task = sio.start_background_task(get_video_frames)
    task_mqtt = sio.start_background_task(mqclient.loop_forever())
    sio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True )
