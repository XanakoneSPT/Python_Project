document.addEventListener('DOMContentLoaded', function() {
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
        const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
        
        currentDateElement.textContent = now.toLocaleDateString('en-US', dateOptions);
        currentTimeElement.textContent = now.toLocaleTimeString('en-US', timeOptions);
    }
    
    // Initialize date and time and update every second
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Start camera
    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: "user"
                } 
            });
            video.srcObject = stream;
            video.style.display = 'block'; // Hiển thị video
            
            // Show stop button, hide start button
            startButton.style.display = 'none';
            stopButton.style.display = 'block';
            
            // Hide any previous status
            statusContainer.style.display = 'none';
            processingIcon.style.display = 'none'; // Ẩn biểu tượng xử lý cho đến khi nhấn nút chụp
            successIcon.style.display = 'none';
            failIcon.style.display = 'none';
            checkInStatus.style.display = 'none';
            checkOutStatus.style.display = 'none';
            
            // Bỏ tự động chụp ảnh - chờ nhấn nút Chụp Ảnh
            // captureInterval = setInterval(captureAndRecognize, 3000);
            
            console.log("Camera started successfully");
            
        } catch (err) {
            console.error("Error accessing camera:", err);
            alert("Error accessing camera. Please make sure your camera is connected and permissions are granted.");
        }
    }
    
    // Stop camera
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
        }
        
        // Clear the capture interval
        if (captureInterval) {
            clearInterval(captureInterval);
            captureInterval = null;
        }
        
        // Show start button, hide stop button
        startButton.style.display = 'block';
        stopButton.style.display = 'none';
        
        // Reset status display
        statusContainer.style.display = 'none';
    }
    
    function captureAndRecognize() {
        if (!stream || processingAttendance) return;
        
        processingAttendance = true;
        
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
        
        // Get image data as base64
        const imageData = canvas.toDataURL('image/jpeg');
        
        // Send to server for face recognition
        sendImageToServer(imageData);
    }
    
    function sendImageToServer(imageData) {
        // Get CSRF token
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Sử dụng URL mới đã tạo để tránh vấn đề với cache
        fetch('/attendance/submit/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_data: imageData
            })
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
                if (data.action === 'check_in') {
                    checkInStatus.style.display = 'inline-block';
                    checkOutStatus.style.display = 'none';
                } else if (data.action === 'check_out') {
                    checkInStatus.style.display = 'none';
                    checkOutStatus.style.display = 'inline-block';
                }
                
                // Play success sound if available
                playSound('success');
                
                // Automatically stop camera after success
                setTimeout(stopCamera, 3000);
            } else {
                // Show fail icon and error message
                processingIcon.style.display = 'none';
                failIcon.style.display = 'block';
                recognitionStatus.textContent = data.message;
                
                // Play failure sound if available
                playSound('failure');
                
                // Reset processing flag after a short delay
                setTimeout(() => {
                    processingAttendance = false;
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            processingAttendance = false;
            
            processingIcon.style.display = 'none';
            failIcon.style.display = 'block';
            recognitionStatus.textContent = 'Server error. Please try again.';
            
            // Wait a bit before resetting flags
            setTimeout(() => {
                processingAttendance = false;
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
    
    // Event listeners
    startButton.addEventListener('click', startCamera);
    stopButton.addEventListener('click', stopCamera);
    
    // Thêm xử lý cho nút Chụp Ảnh
    const captureButton = document.getElementById('captureButton');
    if (captureButton) {
        captureButton.addEventListener('click', function() {
            if (stream) {
                // Chụp ảnh ngay khi nhấn nút
                captureAndRecognize();
            }
        });
    }
    
    // Thêm phím tắt cho việc chụp với phím 'c'
    document.addEventListener('keydown', function(event) {
        if (event.key === 'c' && video.srcObject) {
            // Chụp ảnh khi nhấn 'c' và camera đang chạy
            captureAndRecognize();
        } else if (event.key === 'q' && video.srcObject) {
            // Stop camera if 'q' is pressed and camera is running
            stopCamera();
        }
    });
    
    // Handle page unload to ensure camera is stopped
    window.addEventListener('beforeunload', function() {
        stopCamera();
    });
});