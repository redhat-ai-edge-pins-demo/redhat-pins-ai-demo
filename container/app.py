import cv2
import base64
import io
import numpy as np
from flask_socketio import emit, SocketIO
from flask import Flask, render_template
import sys
import time
import torch


import os

external_host = os.environ.get("EXTERNAL_HOST")
external_port = os.environ.get("EXTERNAL_PORT")



model = torch.hub.load('yolov5', 'custom', path='best.pt', source='local')


app = Flask(__name__, template_folder="/app/templates")
app.secret_key = 'Shadowman42'
sio = SocketIO(app)

dim = (640, 640)
dim_show = (1280, 720)

def get_video_frames():
    #print("START", file=sys.stdout)

    
    if cv2.VideoCapture(1).isOpened():
        cap = cv2.VideoCapture(1)
    elif cv2.VideoCapture(0).isOpened():
        cap = cv2.VideoCapture(0)
    elif cv2.VideoCapture('video.mp4').isOpened():
        cap = cv2.VideoCapture('video.mp4')
    else:
        #print("No video opened", file=sys.stdout)
        sys.exit()

    fps = cap.get(cv2.CAP_PROP_FPS)
    #print(fps)
    #print(cap.get(cv2.CAP_PROP_FRAME_COUNT), file=sys.stdout)
    frame_counter= 0
   


    while True:
        #time.sleep((1000/fps)/1000)
        # Read a frame from the camera
        ret, frame = cap.read()
        frame_counter += 1
        #If the last frame is reached, reset the capture and the frame_counter
        if frame_counter == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            #print("== last frame ==", file=sys.stdout)
            frame_counter = 0 #Or whatever as long as it is the same as next line
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if not ret:
            #print("Error: Could not read a frame.", file=sys.stdout)
            sys.exit

        resized = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)
        results = model(resized)
        if results.pandas().xyxy[0].empty:
            pass
        else:
            for i in results.pandas().xyxy[0]['name']:
                print(i, file=sys.stdout)
        #results.print()
        results_resized = cv2.resize(np.squeeze(results.render()), dim_show, interpolation = cv2.INTER_AREA)
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_bytes = cv2.imencode('.jpg', results_resized)[1]
        stringData = base64.b64encode(frame_bytes).decode('utf-8')
        b64_src = 'data:image/jpeg;base64,'
        stringData = b64_src + stringData
        sio.emit('response_back', stringData, namespace="/")

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
    sio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True )
