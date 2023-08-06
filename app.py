# Import libraries
import cv2 # for reading images, draw bounding boxes
from ultralytics import YOLO 
import gradio as gr

# Define constants
BOX_COLORS = {
    "unchecked": (242, 48, 48),
    "checked": (38, 115, 101),
    "block": (242, 159, 5)
}
BOX_PADDING = 2

# Load models
DETECTION_MODEL = YOLO("models/detector-model.pt") 
CLASSIFICATION_MODEL = YOLO("models/classifier-model.pt") # 0: block, 1: checked, 2: unchecked

def detect(image_path):
    """
    Output inference image with bounding box
    Args:
    - image: to check for checkboxes
    Return: image with bounding boxes drawn 
    """
    image = cv2.imread(image_path)
    if image is None:
        return image
    
    # Predict on image
    results = DETECTION_MODEL.predict(source=image, conf=0.2, iou=0.8) # Predict on image
    boxes = results[0].boxes # Get bounding boxes

    if len(boxes) == 0:
        return image

    # Get bounding boxes
    for box in boxes:
        detection_class_conf = round(box.conf.item(), 2)
        detection_class = list(BOX_COLORS)[int(box.cls)]
        # Get start and end points of the current box
        start_box = (int(box.xyxy[0][0]), int(box.xyxy[0][1]))
        end_box = (int(box.xyxy[0][2]), int(box.xyxy[0][3]))
        box = image[start_box[1]:end_box[1], start_box[0]: end_box[0], :]

        # Determine the class of the box using classification model
        cls_results = CLASSIFICATION_MODEL.predict(source=box, conf=0.5)
        probs = cls_results[0].probs  # cls prob, (num_class, )
        classification_class = list(BOX_COLORS)[2 - int(probs.top1)] 
        classification_class_conf = round(probs.top1conf.item(), 2)

        cls = classification_class if classification_class_conf > 0.9 else detection_class
        
        # 01. DRAW BOUNDING BOX OF OBJECT
        line_thickness = round(0.002 * (image.shape[0] + image.shape[1]) / 2) + 1
        image = cv2.rectangle(img=image, 
                              pt1=start_box, 
                              pt2=end_box,
                              color=BOX_COLORS[cls], 
                              thickness = line_thickness) # Draw the box with predefined colors
        
        # 02. DRAW LABEL
        text = cls + " " + str(detection_class_conf)
        # Get text dimensions to draw wrapping box
        font_thickness =  max(line_thickness - 1, 1)
        (text_w, text_h), _ = cv2.getTextSize(text=text, fontFace=2, fontScale=line_thickness/3, thickness=font_thickness)
        # Draw wrapping box for text
        image = cv2.rectangle(img=image,
                              pt1=(start_box[0], start_box[1] - text_h - BOX_PADDING*2),
                              pt2=(start_box[0] + text_w + BOX_PADDING * 2, start_box[1]),
                              color=BOX_COLORS[cls],
                              thickness=-1)
        # Put class name on image
        start_text = (start_box[0] + BOX_PADDING, start_box[1] - BOX_PADDING)
        image = cv2.putText(img=image, text=text, org=start_text, fontFace=0, color=(255,255,255), fontScale=line_thickness/3, thickness=font_thickness)
        
    return image

iface = gr.Interface(fn=detect, 
                     inputs=gr.inputs.Image(label="Upload scanned document", type="filepath"), 
                     outputs="image")
iface.launch()
