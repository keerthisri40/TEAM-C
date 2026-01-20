import face_recognition
import cv2
import os

class FaceAuthenticator:
    def __init__(self):
        self.known_encodings = []
        self.load_profiles()

    def load_profiles(self):
        profile_dir = 'profiles/'
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        
        for img_name in os.listdir(profile_dir):
            if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(profile_dir, img_name)
                img = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    self.known_encodings.append(encodings[0])
                    print(f"✅ Loaded profile: {img_name}")

    def verify_frame(self, frame):
        """Processes the frame with 0.7 tolerance for dark rooms."""
        try:
            # Ensure the conversion is inside the try block and correctly indented
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            if not self.known_encodings:
                print("❌ ERROR: Profiles not loaded")
                return False

            for encoding in face_encodings:
                # 0.7 tolerance helps in dark lighting conditions
                matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=0.7)
                if True in matches:
                    print("🎯 Match Found!")
                    return True
            return False
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return False