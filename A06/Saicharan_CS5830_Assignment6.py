import os
import uvicorn
import asyncio
from typing import Union
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import uuid
from PIL import Image
import numpy as np
from tensorflow.keras.models import load_model as tf_load_model

UPLOAD_DIR = "uploaded_images/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

MODEL_FILE_PATH = "C:\\Users\\saicharan\\Downloads\\mnist-epoch.hdf5"
model_instance = None

def load_model(model_path: str):
    """Load the trained Keras model from the specified path."""
    return tf_load_model(model_path)

async def get_model_instance():
    """Retrieve the model, loading it if not already loaded."""
    global model_instance
    if model_instance is None:
        model_instance = load_model(MODEL_FILE_PATH)
    return model_instance

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess the image for model prediction."""
    # Convert the image to grayscale and resize to 28x28
    image = image.convert("L").resize((28, 28))
    # Convert the image to a numpy array, flatten, and normalize the pixel values
    image_array = np.array(image).reshape(1, 784) / 255.0
    return image_array

async def predict_digit(image: Image.Image) -> str:
    """Make a prediction on the given image."""
    model = await get_model_instance()
    processed_image = preprocess_image(image)
    prediction = model.predict(processed_image)
    predicted_digit = np.argmax(prediction)
    return str(predicted_digit)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """Handle the uploaded file, make a prediction, and return the result."""
    filename = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())

    image = Image.open(file_path)
    prediction_result = await predict_digit(image)
    
    os.remove(file_path)
    return {"predicted_digit": prediction_result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
