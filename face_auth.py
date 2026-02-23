from deepface import DeepFace
import os
import cv2
import tempfile

class FaceAuthenticator:
    def __init__(self):
        self.profile_path = "profiles"

    def verify_frame(self, frame):
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_path = temp_file.name
                cv2.imwrite(temp_path, frame)

            for filename in os.listdir(self.profile_path):
                profile_img_path = os.path.join(self.profile_path, filename)

                result = DeepFace.verify(
                    img1_path=temp_path,
                    img2_path=profile_img_path,
                    enforce_detection=False,
                    model_name="Facenet",   # You can change to ArcFace later
                    detector_backend="opencv"
                )

                if result["verified"]:
                    print(f"✅ Match found with {filename}")
                    return True

            return False

        except Exception as e:
            print("⚠️ Verification Error:", e)
            return False
