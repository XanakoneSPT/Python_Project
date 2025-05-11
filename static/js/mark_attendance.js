document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startButton = document.getElementById('startButton');
    const captureButton = document.getElementById('captureButton');
    const stopButton = document.getElementById('stopButton');
    const captureControls = document.getElementById('captureControls');
    const statusContainer = document.getElementById('statusContainer');
    const recognitionStatus = document.getElementById('recognitionStatus');
    const processingIcon = document.getElementById('processingIcon');
    const successIcon = document.getElementById('successIcon');
    const failIcon = document.getElementById('failIcon');
    const checkInStatus = document.getElementById('checkInStatus');
    const checkOutStatus = document.getElementById('checkOutStatus');
    
    // Set initial video styles
    video.style.width = '100%';
    video.style.height = 'auto';
    video.style.display = 'block';
    
    // Current date and time display
    updateClock();
    setInterval(updateClock, 1000);
    
    // Video stream
    let stream = null;

    // Start camera
    startButton.addEventListener('click', async function() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: "user"
                } 
            });
            
            video.srcObject = stream;
            video.play();
            
            // Make sure video is visible
            video.style.display = 'block';
            
            // Wait for video to load metadata to ensure dimensions are set
            video.onloadedmetadata = function() {
                console.log("Video dimensions: " + video.videoWidth + "x" + video.videoHeight);
                // Show video and capture controls
                startButton.style.display = 'none';
                captureControls.style.display = 'flex';
            };
            
            // Reset status indicators
            statusContainer.style.display = 'none';
            processingIcon.style.display = 'block';
            successIcon.style.display = 'none';
            failIcon.style.display = 'none';
            checkInStatus.style.display = 'none';
            checkOutStatus.style.display = 'none';
            recognitionStatus.textContent = 'Đang xử lý...';
            
        } catch (err) {
            console.error('Error accessing camera:', err);
            alert('Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập camera của trình duyệt.');
        }
    });

    // Capture image
    captureButton.addEventListener('click', function() {
        captureAndSend();
    });

    // Stop camera
    stopButton.addEventListener('click', function() {
        stopCamera();
        startButton.style.display = 'block';
        captureControls.style.display = 'none';
        statusContainer.style.display = 'none';
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Only process if camera is on
        if (stream && !stream.ended) {
            if (event.key === 'c') {
                captureAndSend();
            } else if (event.key === 'q') {
                stopCamera();
                startButton.style.display = 'block';
                captureControls.style.display = 'none';
            }
        }
    });

    // Function to capture image and send to server
    function captureAndSend() {
        if (!stream || stream.ended) {
            alert('Camera không hoạt động. Vui lòng bật camera trước.');
            return;
        }

        // Display processing status
        statusContainer.style.display = 'block';
        processingIcon.style.display = 'block';
        successIcon.style.display = 'none';
        failIcon.style.display = 'none';
        checkInStatus.style.display = 'none';
        checkOutStatus.style.display = 'none';
        recognitionStatus.textContent = 'Đang xử lý...';

        // Capture frame from video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Convert to base64
        const imageData = canvas.toDataURL('image/jpeg', 0.9);
        
        // Send to server
        sendImageToServer(imageData);
    }

    // Send image to server
    async function sendImageToServer(imageData) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ image_data: imageData })
            });
            
            const data = await response.json();
            
            // Update UI based on response
            if (data.success) {
                // Success
                processingIcon.style.display = 'none';
                successIcon.style.display = 'block';
                failIcon.style.display = 'none';
                recognitionStatus.textContent = data.message;
                
                // Show check-in or check-out status
                if (data.check_in && !data.check_out) {
                    checkInStatus.style.display = 'inline-block';
                    checkOutStatus.style.display = 'none';
                    
                    // Update status in page without reload
                    if (data.check_in_time) {
                        const checkInTimeElement = document.querySelector('.status-time:nth-of-type(1) .badge');
                        if (checkInTimeElement) {
                            checkInTimeElement.textContent = data.check_in_time;
                            checkInTimeElement.className = 'badge bg-success';
                        }
                    }
                } else if (data.check_out) {
                    checkInStatus.style.display = 'none';
                    checkOutStatus.style.display = 'inline-block';
                    
                    // Update status in page without reload
                    if (data.check_out_time) {
                        const checkOutTimeElement = document.querySelector('.status-time:nth-of-type(2) .badge');
                        if (checkOutTimeElement) {
                            checkOutTimeElement.textContent = data.check_out_time;
                            checkOutTimeElement.className = 'badge bg-warning text-dark';
                        }
                    }
                }
                
                // Automatically reload page after 3 seconds to show updated status
                setTimeout(function() {
                    window.location.reload();
                }, 3000);
                
            } else {
                // Failure
                processingIcon.style.display = 'none';
                successIcon.style.display = 'none';
                failIcon.style.display = 'block';
                recognitionStatus.textContent = data.message;
            }
            
        } catch (error) {
            console.error('Error sending data to server:', error);
            processingIcon.style.display = 'none';
            successIcon.style.display = 'none';
            failIcon.style.display = 'block';
            recognitionStatus.textContent = 'Lỗi kết nối đến máy chủ. Vui lòng thử lại.';
        }
    }

    // Stop camera stream
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => {
                track.stop();
            });
            stream = null;
            video.srcObject = null;
        }
    }

    // Update clock
    function updateClock() {
        const now = new Date();
        
        // Update time
        document.getElementById('hour').textContent = padZero(now.getHours());
        document.getElementById('minute').textContent = padZero(now.getMinutes());
        document.getElementById('second').textContent = padZero(now.getSeconds());
        
        // Update date - in Vietnamese format
        const dayNames = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
        const monthNames = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
        
        const dayName = dayNames[now.getDay()];
        const day = padZero(now.getDate());
        const month = monthNames[now.getMonth()];
        const year = now.getFullYear();
        
        document.getElementById('currentDate').textContent = `${dayName}, ${day}/${month}/${year}`;
    }

    // Add leading zero
    function padZero(num) {
        return num < 10 ? '0' + num : num;
    }
});