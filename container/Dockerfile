# Use an official Python runtime as a parent image
#FROM quay.io/hgeaydem/ubi9-jp6-pytorch:pytorch-2.1.0 
FROM fedora:38

# Set the working directory to /app

WORKDIR /app

RUN rm -fr ~/.cache/pip

# Install any dependencies you may need (e.g., OpenCV)
RUN dnf install -y python3-pip python3-devel mesa-libGL git gcc g++ libjpeg libpng libjpeg-devel libpng-devel v4l-utils libv4l conda
RUN git clone https://github.com/ultralytics/yolov5
RUN git config --global --add safe.directory /app/yolov5
RUN pip install websockets flask-socketio dill  torchvision==0.16
RUN sed -i 's/opencv-python/opencv-python-headless/g' yolov5/requirements.txt &&  sed -i 's/torch/#torch/g' yolov5/requirements.txt &&  pip install -r yolov5/requirements.txt

# Copy the current directory contents into the container at /app
ADD video.mp4 /app/
ADD templates /app/templates
ADD static /app/static
COPY app.py /app/
COPY best.pt /app/

# Define the default command to run when the container starts
CMD ["python3", "app.py"]

ENTRYPOINT ["python3", "app.py"]
