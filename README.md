
# Multi Modal Authentication Demo App

## Project Overview
This project is a Streamlit-based web application demonstrating a mutative multimodal biometric authentication model for enhancing data security in online customer banking systems. The project is part of an MSc in Cybersecurity program at the University of Zimbabwe.

## Features
- Multi-modal authentication demonstration
- Facial recognition
- Fingerprint detection

## Python 3.10 pre-installation 

##### For macOS:

1. Visit the official Python downloads page: https://www.python.org/downloads/
2. Scroll down and find Python 3.10.x (where x is the latest minor version)
3. Click on the download link for macOS
4. Once downloaded, open the .pkg file and follow the installation wizard
5. Verify the installation by opening Terminal and typing:
6. Install requirements

##### For Windows:

1. Visit the official Python downloads page: https://www.python.org/downloads/
2. Scroll down and find Python 3.9.x (where x is the latest minor version)
3. Click on the download link for Windows
4. Choose the installer that matches your system (32-bit or 64-bit)
5. Run the downloaded .exe file
6. Important: Check the box that says "Add Python 3.9 to PATH" before clicking "Install Now"
7. Follow the installation wizard
8. Verify the installation by opening Command Prompt and typing:
```
python --version
```

## Demo App Installation
To run this project, you need to have Python installed on your system. Follow these steps:

1. Clone the repository:
```
git clone https://github.com/TheRealSirBen/MultiModalAuthenticationApp.git
```
2. Navigate to the project directory:
```
cd MultiModalAuthenticationApp
```

3. Create and activate virtual environment
#### For macOS:
```
python3.9 -m venv venv
```
```
source venv/bin/activate
```

#### For Windows:
```
python -m venv venv
```
```
venv\Scripts\activate
```
4. Install python libraries
```
pip install -r requirements.txt
```
5. Run application
```
streamlit run 1_Hello.py
```

## Registration Process

Follow these steps to register for the Multi Modal Authentication Demo App:

### Step 1: Application Form

1. On the navigation tab, locate and click the "Registration" button.
2. You will see a form titled "Step 1: Application form".
3. Fill in the following information:
   - Full Name: Type your complete name in the "Enter your full name" field.
   - Email Address: Enter your email address in the "Enter your email address" field.
   - Password: Create and enter a secure password in the "Set up your password" field.
4. After filling all fields, click the "Submit" button.
5. Wait for the system to process your information. If successful, you'll automatically move to Step 2.

Note: If you see a warning that the email already exists, you'll need to use a different email address.

### Step 2: Facial Recognition

1. You will see a header "Step 2: Register my face".
2. The app will access your device's camera. Ensure your camera is working and allow access if prompted.
3. You'll see a live video feed from your camera.
4. Position your face in the frame, ensuring good lighting and a clear view of your face.
5. Click the "Take Selfie" button to capture an image.
6. Wait for the system to process the image. If a face is detected, you'll see a success message.
7. Repeat this process until you've taken the required number of selfies (usually 3-5).
8. The camera will automatically stop when enough images are captured.
9. Wait while the system uploads your images to cloud storage. You'll see a progress bar.
10. Once complete, a "Continue to Fingerprint Registrations" button will appear. Click it to proceed to Step 3.

### Step 3: Fingerprint Registration

1. You'll see a header "Step 3: Register my fingerprints".
2. Choose your preferred method:
   - "Upload Images" if you have existing fingerprint scans.
   - "Scan my hands" if you're using a fingerprint scanner (note: this option may not be available in all setups).

For "Upload Images":
1. You'll be prompted to upload images for each finger, starting with your left little finger.
2. Click "Choose a file" to select an image from your device.
3. After selecting an image, click "Upload Fingerprint image".
4. Wait for the upload confirmation before proceeding to the next finger.
5. Repeat this process for all ten fingers.

For "Scan my hands" (if available):
1. Follow the on-screen instructions to scan each fingerprint using the provided scanner.
2. Wait for each scan to be processed before moving to the next finger.

3. As you upload or scan, you'll see the fingerprint images appear in the "Collected Fingerprints" section.
4. Once all ten fingerprints are registered, a "Proceed to registration completion" button will appear. Click it.

### Registration Complete

1. You'll see a "Registration complete" message.
2. You can now proceed to log in using your registered credentials.

If you need to start over, click the "New registration" button at the bottom of the page.

Remember: Ensure you're in a well-lit area for facial recognition and that your fingers are clean and dry for fingerprint scanning. If you encounter any issues, check the error messages and try again.

## Login Process

The login process in this Multi Modal Authentication Demo App consists of several steps:

1. **Password Authentication**
   - Users enter their email address and password.
   - The system verifies the credentials against the database.
   - If successful, it proceeds to the next step; otherwise, an error message is displayed.

2. **Liveness Detection Check**
   - The app uses the device's camera to perform a liveness detection test.
   - Users are prompted to perform specific hand gestures (e.g., "right hand open", "left hand pointer").
   - The system uses MediaPipe and a custom KeyPointClassifier to detect and classify hand gestures.
   - Face detection is also performed to ensure the user's face is visible.
   - Multiple gestures are requested to complete the liveness check.
   - Images are captured and saved during successful gesture detections.

3. **Facial Recognition Authentication**
   - The system compares the facial images captured during liveness detection with the user's registered face images.
   - A similarity matrix is created, and a confidence score is calculated.
   - If the facial recognition is successful (more than 66% of images match with high confidence), the user proceeds to the next step.

4. **Fingerprint Recognition Authentication**
   - Users can choose between uploading fingerprint images or using a fingerprint scanner.
   - For image upload:
     - The system randomly selects a finger for verification.
     - Users upload an image of the requested finger.
     - The uploaded fingerprint is compared with the stored fingerprint for that finger.
   - Multiple fingerprint checks may be required.
   - Failed attempts are tracked, and too many failures result in a logout.

5. **Successful Login**
   - After passing all authentication steps, users are granted access to their account.

Throughout the process, the app uses session state to manage the user's progress and store temporary data. It also handles alerts and messages to keep the user informed about the authentication status.

The login process combines multiple biometric factors (face and fingerprint) with traditional password authentication to enhance security. The liveness detection step adds an extra layer of protection against spoofing attempts.

## Login Process

The login process in this Multi Modal Authentication Demo App consists of several steps:

1. **Password Authentication**
   - Users enter their email address and password.
   - The system verifies the credentials against the database.
   - If successful, it proceeds to the next step; otherwise, an error message is displayed.

2. **Liveness Detection Check**
   - The app uses the device's camera to perform a liveness detection test.
   - Users are prompted to perform specific hand gestures (e.g., "right hand open", "left hand pointer").
   - The system uses MediaPipe and a custom KeyPointClassifier to detect and classify hand gestures.
   - Face detection is also performed to ensure the user's face is visible.
   - Multiple gestures are requested to complete the liveness check.
   - Images are captured and saved during successful gesture detections.

3. **Facial Recognition Authentication**
   - The system compares the facial images captured during liveness detection with the user's registered face images.
   - A similarity matrix is created, and a confidence score is calculated.
   - If the facial recognition is successful (more than 66% of images match with high confidence), the user proceeds to the next step.

4. **Fingerprint Recognition Authentication**
   - Users can choose between uploading fingerprint images or using a fingerprint scanner.
   - For image upload:
     - The system randomly selects a finger for verification.
     - Users upload an image of the requested finger.
     - The uploaded fingerprint is compared with the stored fingerprint for that finger.
   - Multiple fingerprint checks may be required.
   - Failed attempts are tracked, and too many failures result in a logout.

5. **Successful Login**
   - After passing all authentication steps, users are granted access to their account.

Throughout the process, the app uses session state to manage the user's progress and store temporary data. It also handles alerts and messages to keep the user informed about the authentication status.

The login process combines multiple biometric factors (face and fingerprint) with traditional password authentication to enhance security. The liveness detection step adds an extra layer of protection against spoofing attempts.

