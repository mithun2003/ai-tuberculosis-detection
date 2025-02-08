from fastapi import FastAPI, File, UploadFile, HTTPException
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import cv2
from fastapi.middleware.cors import CORSMiddleware
import gdown
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

file_id = "1QyQp-Ez9xKEcl1-b_Ewmt4wdAJkekOtc"
# Path where the model file should be saved
file_path = "tb_cnn_model.h5"


# Create the URL to the Google Drive file
url = f"https://drive.google.com/uc?id={file_id}"

# Check if the file already exists
if not os.path.exists(file_path):
    # Download the file if it doesn't exist
    gdown.download(url, file_path, quiet=False)
else:
    print("Model file already exists. Skipping download.")
# Load the pre-trained Tuberculosis detection model
model = tf.keras.models.load_model("tb_cnn_model.h5")

# Define image dimensions
IMG_HEIGHT = 224
IMG_WIDTH = 224

# Initialize FastAPI app
app = FastAPI()
# ✅ Add CORS Middleware to Allow Frontend Requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # ✅ Allow all origins (change to frontend domain in production)
    allow_credentials=True,
    allow_methods=["*"],  # ✅ Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # ✅ Allow all headers
)


frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve frontend static files (HTML, CSS, JS) from the "frontend" directory
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Main route to serve the index.html
@app.get("/")
def read_root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Serve styles.css at the /styles.css path
@app.get("/styles.css")
def read_styles():
    return FileResponse(os.path.join(frontend_dir, "styles.css"))

# Serve script.js at the /script.js path
@app.get("/script.js")
def read_script():
    return FileResponse(os.path.join(frontend_dir, "script.js"))

# Function to validate if image is a chest X-ray
def is_xray_image(image: np.array) -> bool:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    return np.mean(edges) < 10  # X-ray images usually have low edge intensity


@app.post("/predict")
async def predict_tb(file: UploadFile = File(...)):
    try:
        print(file.filename)
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image = image.resize((IMG_WIDTH, IMG_HEIGHT))
        image_array = np.array(image) / 255.0
        image_array = np.expand_dims(image_array, axis=0)

        # Convert to OpenCV format for X-ray validation
        # image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        # if not is_xray_image(image_cv):
        #     raise HTTPException(status_code=400, detail="Uploaded image is not a valid chest X-ray.")

        # Predict TB probability
        probability = round(float(model.predict(image_array)[0][0] * 100), 2)

        return {"TB_Probability": probability}
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}


xray_classifier = tf.keras.applications.VGG16(weights="imagenet")  # Pretrained Model


# Function to Check if Image is a Chest X-ray
def is_xray(image_bytes):
    img_array = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (224, 224))
    img = np.expand_dims(img, axis=0)
    img = tf.keras.applications.vgg16.preprocess_input(img)

    # Predict Image Type
    predictions = xray_classifier.predict(img)
    decoded_preds = tf.keras.applications.vgg16.decode_predictions(predictions, top=1)

    # Check if Image is a Chest X-ray
    label = decoded_preds[0][0][1].lower()  # Example: 'chest'
    if "chest" in label or "x-ray" in label:
        return True  # It's an X-ray
    return False  # Not an X-ray


@app.post("/predict_tb")
async def predict_tbs(image: UploadFile = File(...)):
    # Validate File Type
    try:
        print(image.filename)
        if not image.filename.endswith((".jpg", ".png", ".jpeg")):
            raise HTTPException(
                status_code=400, detail="Invalid file type. Please upload a JPG or PNG."
            )

        # Read Image
        contents = await image.read()

        # Check if the Image is a Chest X-ray
        # if not is_xray(contents):
        #     raise HTTPException(status_code=400, detail="Uploaded image is not a valid Chest X-ray.")

        # Process Image for TB Detection
        img_array = np.asarray(bytearray(contents), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (224, 224)) / 255.0
        img = np.expand_dims(img, axis=0)

        # Predict TB Probability
        probability = round(float(model.predict(img)[0][0]) * 100, 2)
        return {"probability": probability}
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}
