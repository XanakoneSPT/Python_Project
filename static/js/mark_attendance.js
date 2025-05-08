document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const captureButton = document.getElementById('captureButton');
    const statusContainer = document.getElementById('statusContainer');
    const processingIcon = document.getElementById('processingIcon');
    const successIcon = document.getElementById('successIcon');
    const failIcon = document.getElementById('failIcon');
    const recognitionStatus = document.getElementById('recognitionStatus');
    const checkInStatus = document.getElementById('checkInStatus');
    const checkOutStatus = document.getElementById('checkOutStatus');
    const currentDateElement = document.getElementById('currentDate');
    const currentTimeElement = document.getElementById('currentTime');
    
    let stream = null;
    
    // Update date and time
    function updateDateTime() {
        const now = new Date();
        const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
        
        currentDateElement.textContent = now.toLocaleDateString('en-US', dateOptions);
        currentTimeElement.textContent = now.toLocaleTimeString('en-US', timeOptions);
    }
    
    // Update date and time every second
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Start camera
    startButton.addEventListener('click', function() {
        startCamera();
    });
    
    // Stop camera
    stopButton.addEventListener('click', function() {
        stopCamera();
    });
    
    // Capture image
    captureButton.addEventListener('click', function() {
        captureAndRecognize();
    });
    
    function startCamera() {
        // Access the webcam
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(mediaStream) {
                stream = mediaStream;
                video.srcObject = stream;
                
                // Show stop button and capture button, hide start button
                startButton.style.display = 'none';
                stopButton.style.display = 'inline-block';
                captureButton.style.display = 'inline-block';
                
                // Hide any previous status
                statusContainer.style.display = 'none';
                successIcon.style.display = 'none';
                failIcon.style.display = 'none';
                processingIcon.style.display = 'block';
                checkInStatus.style.display = 'none';
                checkOutStatus.style.display = 'none';
                
                // Make sure video is visible and canvas is hidden
                video.style.display = 'block';
                canvas.style.display = 'none';
            })
            .catch(function(err) {
                alert('Error accessing camera: ' + err.message);
            });
    }
    
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
        }
        
        // Reset display of video and canvas
        video.style.display = 'block';
        canvas.style.display = 'none';
        
        // Show start button, hide stop button and capture button
        startButton.style.display = 'block';
        stopButton.style.display = 'none';
        captureButton.style.display = 'none';
    }
    
    function captureAndRecognize() {
        // Show status container
        statusContainer.style.display = 'block';
        recognitionStatus.textContent = 'Processing...';
        processingIcon.style.display = 'block';
        successIcon.style.display = 'none';
        failIcon.style.display = 'none';
        
        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw video frame to canvas
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Show the canvas with captured image
        video.style.display = 'none';
        canvas.style.display = 'block';
        
        // Get image data as base64
        const imageData = canvas.toDataURL('image/jpeg');
        
        // Send to server for face recognition
        sendImageToServer(imageData);
        
        // Disable capture button while processing
        captureButton.disabled = true;
    }
    
    function sendImageToServer(imageData) {
        // Get CSRF token
        const csrftoken = getCookie('csrftoken');
        
        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                image_data: imageData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Success
                processingIcon.style.display = 'none';
                successIcon.style.display = 'block';
                recognitionStatus.textContent = data.message;
                
                // Show check-in or check-out status
                if (data.action === 'check_in') {
                    checkInStatus.style.display = 'inline-block';
                    checkOutStatus.style.display = 'none';
                } else if (data.action === 'check_out') {
                    checkInStatus.style.display = 'none';
                    checkOutStatus.style.display = 'inline-block';
                }
                
                // Play success sound if available
                playSound('success');
                
                // Auto stop camera after success
                setTimeout(stopCamera, 3000);
            } else {
                // Failure
                processingIcon.style.display = 'none';
                failIcon.style.display = 'block';
                recognitionStatus.textContent = data.message;
                
                // Play failure sound if available
                playSound('failure');
                
                // Re-enable capture button for retry
                captureButton.disabled = false;
                
                // Switch back to video after 2 seconds
                setTimeout(() => {
                    video.style.display = 'block';
                    canvas.style.display = 'none';
                }, 2000);
            }
        })
        .catch(error => {
            processingIcon.style.display = 'none';
            failIcon.style.display = 'block';
            recognitionStatus.textContent = 'Error: ' + error.message;
            
            // Re-enable capture button for retry
            captureButton.disabled = false;
            
            // Switch back to video after 2 seconds
            setTimeout(() => {
                video.style.display = 'block';
                canvas.style.display = 'none';
            }, 2000);
        });
    }
    
    // Function to play sounds
    function playSound(type) {
        try {
            const audio = new Audio();
            if (type === 'success') {
                audio.src = '/static/sounds/success.mp3';
            } else {
                audio.src = '/static/sounds/failure.mp3';
            }
            audio.play();
        } catch (e) {
            console.log('Could not play sound:', e);
        }
    }
    
    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        if (event.key === 'q' && video.srcObject) {
            // Stop camera if 'q' is pressed and camera is running
            stopCamera();
        } else if (event.key === 'c' && video.srcObject) {
            // Capture image if 'c' is pressed and camera is running
            captureAndRecognize();
        }
    });
});