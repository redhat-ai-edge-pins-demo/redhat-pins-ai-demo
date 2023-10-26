# Use an official Python runtime as a parent image
FROM registry.access.redhat.com/ubi9/ubi:latest

# Set the working directory to /app
WORKDIR /app

ADD video.mp4 .
ADD templates .
ADD static .

# Install any dependencies you may need (e.g., OpenCV)
RUN dnf install -y python3-pip mesa-libGL git 
RUN git clone https://github.com/ultralytics/yolov5
RUN pip install websockets flask-socketio dill 
RUN  sed -i 's/opencv-python/opencv-python-headless/g' yolov5/requirements.txt &&  pip install -r yolov5/requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Define the default command to run when the container starts
CMD ["python3", "app.py"]
