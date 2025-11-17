from django.shortcuts import render
from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
import os
import base64
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .models import Prediction


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "detector", "keras_model.h5")
LABELS_PATH = os.path.join(BASE_DIR, "detector", "labels.txt")

MODEL = load_model(MODEL_PATH, compile=False)
CLASS_NAMES = [line.strip() for line in open(LABELS_PATH)]


def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    predictions = Prediction.objects.all().order_by('-created_at')
    return render(request, "detector/admin_dashboard.html", {"predictions": predictions})


@login_required
def home(request):
    result_text = None
    image_base64 = None
    error = None

    if request.method == "POST" and request.FILES.get("image"):
        imgfile = request.FILES["image"]

        try:
            # Reset file pointer and read bytes for Base64
            imgfile.seek(0)
            img_bytes = imgfile.read()
            image_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # Reset again for PIL
            imgfile.seek(0)
            image = Image.open(imgfile).convert("RGB")
            image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
            image_array = np.asarray(image)
            normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            data[0] = normalized_image_array

            # Predict
            prediction = MODEL.predict(data)
            index = np.argmax(prediction)
            class_name = CLASS_NAMES[index]
            confidence_score = float(prediction[0][index])

            Prediction.objects.create(
                user=request.user,
                image=imgfile,
                result=class_name,
                confidence=confidence_score*100  # store as percentage
            )

            if "ai" in class_name.lower():
                result_text = f"This looks like AI-generated art with {confidence_score*100:.2f}% confidence."
            else:
                result_text = f"This looks like real art with {confidence_score*100:.2f}% confidence."

        except Exception:
            error = "Error processing the image. Make sure it is a valid image file."

    return render(request, "detector/upload.html", {
        "result_text": result_text,
        "image_base64": image_base64,
        "error": error
    })
