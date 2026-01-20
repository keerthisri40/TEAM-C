import face_recognition
import cv2

# Test if your saved photo is actually readable
try:
    img = face_recognition.load_image_file("profiles/keer.jpg")
    encoding = face_recognition.face_encodings(img)
    if not encoding:
        print("❌ CRITICAL ERROR: The AI cannot find a face in 'profiles/keer.jpg'. Please use a clearer, front-facing photo.")
    else:
        print("✅ SUCCESS: Your profile photo is perfect.")
except Exception as e:
    print(f"❌ FILE ERROR: Could not find 'profiles/keer.jpg'. Check your folder names.")