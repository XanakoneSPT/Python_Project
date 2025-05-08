import face_recognition
import cv2
import numpy as np
import json
from .models import Employee, FaceEncoding, AttendanceRecord
from django.utils import timezone

def capture_face_with_button():
    """Capture face using either keyboard press or button click"""
    video_capture = cv2.VideoCapture(0)
    captured_frame = None
    face_encoding = None
    
    print("Press SPACE to capture or 'q' to quit")
    
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
            
        # Convert BGR to RGB for processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Draw rectangle around faces
        display_frame = frame.copy()
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Add text instructions
        cv2.putText(display_frame, "Press SPACE to capture", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, "Press 'q' to quit", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Display the resulting frame
        cv2.imshow('Camera - Face Recognition', display_frame)
        
        # Check for key presses
        key = cv2.waitKey(1) & 0xFF
        
        # If space is pressed and there's a face, capture it
        if key == 32:  # Space key
            if len(face_locations) > 0:
                # Get face encodings
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if len(face_encodings) > 0:
                    captured_frame = frame.copy()
                    face_encoding = face_encodings[0]
                    print("Face captured successfully!")
                    break
                else:
                    print("Could not encode face. Please try again.")
            else:
                print("No face detected. Please position yourself in front of the camera.")
        
        # If q is pressed, quit
        elif key == ord('q'):
            print("Face capture cancelled.")
            break
    
    video_capture.release()
    cv2.destroyAllWindows()
    return face_encoding, captured_frame

def register_employee_face(employee_id):
    """Register face for an employee"""
    try:
        print(f"Starting face registration for employee ID: {employee_id}")
        employee = Employee.objects.get(id=employee_id)
        print(f"Employee found: {employee.first_name} {employee.last_name}")
        
        print("Please look at the camera and press SPACE to capture your face")
        face_encoding, image = capture_face_with_button()
        
        if face_encoding is None or image is None:
            print("No face captured or capture cancelled")
            return False, "No face captured or capture cancelled"
            
        print("Face encoding obtained successfully")
        
        # Create directory if it doesn't exist
        import os
        os.makedirs('media/employee_profiles', exist_ok=True)
        
        # Save image first to make sure we can write to disk
        image_path = f'employee_profiles/{employee.employee_id}.jpg'
        full_path = f'media/{image_path}'
        print(f"Attempting to save image to: {os.path.abspath(full_path)}")
        success = cv2.imwrite(full_path, image)
        print(f"Image save result: {'Success' if success else 'Failed'}")
        
        if not success:
            return False, "Failed to save image file"
        
        # Save the encoding
        print("Saving face encoding to database")
        face_encoding_obj = FaceEncoding(employee=employee)
        face_encoding_obj.set_encoding(face_encoding)
        face_encoding_obj.save()
        print("Face encoding saved successfully")
        
        # Update employee profile image
        if employee.profile_image is None or employee.profile_image == '':
            employee.profile_image = image_path
            employee.save()
            print("Employee profile updated with image path")
            
        return True, "Face registered successfully"
    except Exception as e:
        import traceback
        print(f"Error in register_employee_face: {e}")
        print(traceback.format_exc())
        return False, str(e)

def recognize_face_for_attendance():
    """Recognize face and mark attendance"""
    print("Please look at the camera and press SPACE to capture your face for attendance")
    face_encoding, _ = capture_face_with_button()
    
    if face_encoding is None:
        return False, "No face captured or capture cancelled"
        
    # Get all active employees with face encodings
    all_face_encodings = FaceEncoding.objects.filter(employee__is_active=True)
    
    for db_encoding in all_face_encodings:
        # Get the stored encoding
        stored_encoding = np.array(db_encoding.get_encoding())
        
        # Compare faces
        matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)
        
        if matches[0]:
            employee = db_encoding.employee
            today = timezone.now().date()
            now = timezone.now()
            
            # Check if attendance already exists for today
            attendance, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'check_in_time': now,
                    'status': 'present',
                    'verification_method': 'face'
                }
            )
            
            if not created:
                # If already checked in, mark checkout time
                if attendance.check_out_time is None:
                    attendance.check_out_time = now
                    attendance.calculate_hours()
                    attendance.save()
                    return True, f"Check-out recorded for {employee.first_name} {employee.last_name}"
                else:
                    return False, f"{employee.first_name} {employee.last_name} already checked out today"
            else:
                return True, f"Check-in recorded for {employee.first_name} {employee.last_name}"
                
    return False, "No matching face found"

# Optional: Add a GUI button for capturing
def capture_with_gui_button():
    """Create a simple GUI with a capture button"""
    import tkinter as tk
    from PIL import Image, ImageTk
    
    def update_frame():
        ret, frame = video_capture.read()
        if ret:
            # Convert to RGB for display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # Draw rectangles around faces
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
            # Convert to ImageTk format
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            panel.imgtk = imgtk
            panel.config(image=imgtk)
        
        # Update again after 10ms if window still exists
        if root.winfo_exists():
            root.after(10, update_frame)
    
    def on_capture():
        nonlocal captured_encoding, captured_image
        ret, frame = video_capture.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if len(face_locations) > 0:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if len(face_encodings) > 0:
                    captured_encoding = face_encodings[0]
                    captured_image = frame.copy()
                    status_label.config(text="Face captured successfully!")
                    root.after(1000, root.quit)
                else:
                    status_label.config(text="Could not encode face. Please try again.")
            else:
                status_label.config(text="No face detected. Please position yourself properly.")
    
    def on_cancel():
        nonlocal cancelled
        cancelled = True
        root.quit()
    
    # Initialize variables
    captured_encoding = None
    captured_image = None
    cancelled = False
    
    # Initialize camera
    video_capture = cv2.VideoCapture(0)
    
    # Create GUI
    root = tk.Tk()
    root.title("Face Capture")
    
    # Create video panel
    panel = tk.Label(root)
    panel.pack(padx=10, pady=10)
    
    # Status label
    status_label = tk.Label(root, text="Position your face in the frame")
    status_label.pack(pady=5)
    
    # Button frame
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    
    # Capture button
    capture_btn = tk.Button(btn_frame, text="Capture", command=on_capture, 
                           bg="green", fg="white", width=10, height=2)
    capture_btn.pack(side=tk.LEFT, padx=10)
    
    # Cancel button
    cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel,
                          bg="red", fg="white", width=10, height=2)
    cancel_btn.pack(side=tk.LEFT, padx=10)
    
    # Start video update
    update_frame()
    
    # Start main loop
    root.mainloop()
    
    # Cleanup
    video_capture.release()
    
    if cancelled:
        return None, None
    
    return captured_encoding, captured_image