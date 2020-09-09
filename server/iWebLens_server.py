import io

import flask
from flask import *
import cv2
import numpy as np
import json
from PIL import Image

app = Flask(__name__)  # The current module

@app.route("/api/detect", methods=["POST"])
def detect():
    # Accept and process the image
    img = request.files['image'].read()
    image = Image.open(io.BytesIO(img))
    # cvImg = cv2.resize(image, None, fx=0.4, fy=0.4)
    # height, width, channels = image.shape

    # setup the neural network
    net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3-tiny.cfg")
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    # Detect object
    image2NP = np.array(image)
    image = image2NP.copy()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Process the output
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            #Filtering noises
            if confidence > 0.0:
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Need to make a list of dict
    resultList = []
    for i in range(len(class_ids)):
        result = {}
        result["label"] = str(classes[class_ids[i]])
        result["accuracy"] = str(confidences[i])
        resultList.append(result)
    resultDict = {}
    resultDict["Objects"] = resultList

    # return as json
    return flask.Response(response=json.dumps(resultDict), status=200, mimetype="application/json")


if __name__ == "__main__":
    app.run(threaded = True, debug=False, host="0.0.0.0")
