import io
import os
import time
from PIL import Image
import numpy as np
import uvicorn
import psutil
from fastapi import FastAPI, UploadFile, File, Request
from prometheus_client import Counter, Gauge, start_http_server
from prometheus_fastapi_instrumentator import Instrumentator

# Initialize FastAPI application
app = FastAPI()

# Instrument FastAPI application for Prometheus monitoring
Instrumentator().instrument(app).expose(app)

# Define Prometheus metrics
REQUEST_COUNTER = Counter(
    'api_requests_total', 'Total number of API requests', ['client_ip']
)
RUN_TIME_GAUGE = Gauge('api_run_time_seconds', 'Running time of the API')
TL_TIME_GAUGE = Gauge(
    'api_tl_time_microseconds', 'Effective processing time per character'
)
MEMORY_USAGE_GAUGE = Gauge('api_memory_usage_kb', 'Memory usage of the API process')
CPU_USAGE_GAUGE = Gauge('api_cpu_usage_percent', 'CPU usage of the API process')
NETWORK_BYTES_SENT_GAUGE = Gauge(
    'api_network_bytes_sent', 'Network bytes sent by the API process'
)
NETWORK_BYTES_RECV_GAUGE = Gauge(
    'api_network_bytes_received', 'Network bytes received by the API process'
)

def preprocess_image(image):
    'Resize and convert the image to grayscale'
    resized_image = image.resize((28, 28)).convert("L")
    image_array = np.array(resized_image)
    flattened_image = image_array.flatten()
    return flattened_image

def predict_digit_from_image(data):
    'Predict digit from image data'
    if data.size != (28, 28):
        data = preprocess_image(data).reshape((1, 784))
    else:
        data = data.convert("L").reshape((1, 784))
    return str(np.random.randint(10))  # Placeholder for predicted digit

def process_memory_usage():
    'Get current process memory usage in kilobytes'
    return psutil.virtual_memory().used / 1024

@app.post("/predict/")
async def predict_digit_api(request: Request, file: UploadFile = File(...)):
    'Predict digit from uploaded image file'

    start_time = time.time()                                    # Start time of API call
    initial_memory_usage = process_memory_usage()                # Initial memory usage
    
    contents = await file.read()                                # Read image file contents
    image = Image.open(io.BytesIO(contents))                    # Open image using PIL
    
    client_ip = request.client.host                             # Get client's IP address
    
    network_io_counters = psutil.net_io_counters()              # Network I/O counters
    
    predicted_digit = predict_digit_from_image(image)           # Predict digit in image
    
    cpu_percent = psutil.cpu_percent(interval=1)                # CPU usage percentage
    final_memory_usage = process_memory_usage()                 # Final memory usage
    
    CPU_USAGE_GAUGE.set(cpu_percent)                            # Set CPU usage gauge
    MEMORY_USAGE_GAUGE.set(abs(final_memory_usage - initial_memory_usage))  # Set memory usage gauge
    NETWORK_BYTES_SENT_GAUGE.set(network_io_counters.bytes_sent)           # Set network bytes sent gauge
    NETWORK_BYTES_RECV_GAUGE.set(network_io_counters.bytes_recv)           # Set network bytes received gauge
    
    # Calculate API running time
    end_time = time.time()
    run_time = end_time - start_time
    
    # Record API usage metrics
    REQUEST_COUNTER.labels(client_ip).inc()                      # Increment request counter             
    RUN_TIME_GAUGE.set(run_time)                                # Set running time gauge
    
    # Calculate T/L time
    input_length = len(contents)
    tl_time = (run_time / input_length) * 1e6                    # microseconds per pixel
    TL_TIME_GAUGE.set(tl_time)                                  # Set T/L time gauge
    
    return {"predicted_digit": predicted_digit}

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8001)
    
    # Run FastAPI application
    uvicorn.run(
        "main:app",
        reload=True,
        workers=1,
        host="0.0.0.0",
        port=8002
    )