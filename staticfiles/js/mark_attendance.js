// DOM Elements
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const statusContainer = document.getElementById('statusContainer');
const processingIcon = document.getElementById('processingIcon');
const successIcon = document.getElementById('successIcon');
const failIcon = document.getElementById('failIcon');
const recognitionStatus = document.getElementById('recognitionStatus');
const checkInStatus = document.getElementById('checkInStatus');
const checkOutStatus = document.getElementById('checkOutStatus');
const currentDateElement = document.getElementById('currentDate');
const currentTimeElement = document.getElementById('currentTime');

// Global variables
let stream = null;
let captureInterval = null;
let processingAttendance = false;

// Update date and time
function updateDateTime() {
    const now = new Date();
    
    const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    currentDateElement.textContent = now.toLocaleDateString('en-US', dateOptions);
    
    const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
    currentTimeElement.textContent = now.toLocaleTimeString('en-US', timeOptions);
}

// Initialize date and time and update every second
updateDateTime();
setInterval(updateDateTime, 1000);

// Start video stream
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user"
            } 
        });
        video.srcObject = stream;
        startButton.style.display = 'none';
        stopButton.style.display = 'block';
        
        // After camera starts, begin automatic capture every 2 seconds
        captureInterval = setInterval(captureAndSendImage, 2000);
        
    } catch (err) {
        console.error("Error accessing camera:", err);
        alert("Error accessing camera. Please make sure your camera is connected and permissions are granted.");
    }
}

// Stop video stream
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        startButton.style.display = 'block';
        stopButton.style.display = 'none';
        
        // Clear the capture interval
        if (captureInterval) {
            clearInterval(captureInterval);
            captureInterval = null;
        }
        
        // Reset status display
        statusContainer.style.display = 'none';
        processingIcon.style.display = 'block';
        successIcon.style.display = 'none';
        failIcon.style.display = 'none';
        checkInStatus.style.display = 'none';
        checkOutStatus.style.display = 'none';
        recognitionStatus.textContent = 'Processing...';
    }
}

// Capture image from video and send for processing
function captureAndSendImage() {
    if (!stream || processingAttendance) return;
    
    // Show status container
    statusContainer.style.display = 'block';
    
    const context = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw the current video frame to the canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to data URL
    const imageData = canvas.toDataURL('image/jpeg');
    
    // Now send this image to the server for face recognition
    sendImageForAttendance(imageData);
}

// Send image to server for attendance marking
function sendImageForAttendance(imageData) {
    if (processingAttendance) return;
    
    processingAttendance = true;
    processingIcon.style.display = 'block';
    successIcon.style.display = 'none';
    failIcon.style.display = 'none';
    recognitionStatus.textContent = 'Processing...';
    
    // Get CSRF token from the form
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Send image data to server
    fetch('/face_attendance/mark-attendance/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `image_data=${encodeURIComponent(imageData)}`
    })
    .then(response => response.json())
    .then(data => {
        processingAttendance = false;
        
        if (data.success) {
            // Show success icon and message
            processingIcon.style.display = 'none';
            successIcon.style.display = 'block';
            recognitionStatus.textContent = data.message;
            
            // Clear interval to stop capturing while showing the success message
            if (captureInterval) {
                clearInterval(captureInterval);
                captureInterval = null;
            }
            
            // Display the status badge
            if (data.status === 'check_in') {
                checkInStatus.style.display = 'inline-block';
                checkOutStatus.style.display = 'none';
            } else if (data.status === 'check_out') {
                checkInStatus.style.display = 'none';
                checkOutStatus.style.display = 'inline-block';
            }
            
            // Automatically stop camera after successful attendance
            setTimeout(() => {
                stopCamera();
                // Optionally reload the page to update attendance status display
                // window.location.reload();
            }, 3000);
            
        } else {
            // Show fail icon and error message
            processingIcon.style.display = 'none';
            failIcon.style.display = 'block';
            recognitionStatus.textContent = data.message;
            
            // Wait a bit before trying again
            setTimeout(() => {
                processingAttendance = false;
                // Reset icons
                processingIcon.style.display = 'block';
                failIcon.style.display = 'none';
                recognitionStatus.textContent = 'Processing...';
            }, 2000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        processingAttendance = false;
        
        // Show error state
        processingIcon.style.display = 'none';
        failIcon.style.display = 'block';
        recognitionStatus.textContent = 'Server error. Please try again.';
        
        // Reset after a timeout
        setTimeout(() => {
            statusContainer.style.display = 'none';
        }, 3000);
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    startButton.addEventListener('click', startCamera);
    stopButton.addEventListener('click', stopCamera);
    
    // Handle keypress to stop camera with 'q' key
    document.addEventListener('keydown', function(event) {
        if (event.key.toLowerCase() === 'q') {
            stopCamera();
        }
    });
});

// Handle page unload to ensure camera is stopped
window.addEventListener('beforeunload', function() {
    stopCamera();
});