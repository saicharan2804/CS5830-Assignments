import io
import sys
import numpy as np
import argparse
from PIL import Image
from fastapi import FastAPI, UploadFile, File
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Gauge

# Optional imports for future use, currently commented out
# import keras
# import keras.models as models
# import matplotlib.pyplot as plt