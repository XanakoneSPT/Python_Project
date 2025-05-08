        // Radio button toggle for employee selection
        document.querySelectorAll('input[name="registerType"]').forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'existing') {
                    document.getElementById('existingEmployeeSection').style.display = 'block';
                    document.getElementById('newEmployeeSection').style.display = 'none';
                    document.getElementById('is_new_employee').value = 'false';
                    document.getElementById('is_new_employee_upload').value = 'false';
                } else {
                    document.getElementById('existingEmployeeSection').style.display = 'none';
                    document.getElementById('newEmployeeSection').style.display = 'block';
                    document.getElementById('is_new_employee').value = 'true';
                    document.getElementById('is_new_employee_upload').value = 'true';
                }
            });
        });

        // Function to collect form data
        function collectFormData() {
            if (document.getElementById('newEmployee').checked) {
                const formData = {
                    employee_id: document.getElementById('employee_id_new').value,
                    first_name: document.getElementById('first_name').value,
                    last_name: document.getElementById('last_name').value,
                    email: document.getElementById('email').value,
                    phone: document.getElementById('phone').value,
                    position: document.getElementById('position').value,
                    date_hired: document.getElementById('date_hired').value,
                    department: document.getElementById('department').value,
                    is_active: document.getElementById('is_active').checked
                };
                
                document.getElementById('employee_form_data').value = JSON.stringify(formData);
                document.getElementById('employee_form_data_upload').value = JSON.stringify(formData);
                return true;
            }
            return true;
        }

        // Camera functionality
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const imageDataInput = document.getElementById('image_data');
        const cameraForm = document.getElementById('cameraForm');
        const imagePreview = document.getElementById('imagePreview');
        let stream = null;

        // Function to start camera
        function startCamera() {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(videoStream => {
                    stream = videoStream;
                    video.srcObject = stream;
                    video.play();
                })
                .catch(err => {
                    console.error("Error accessing the camera: ", err);
                    alert("Unable to access the camera. Please check permissions or try the upload option.");
                });
        }

        // Function to stop camera
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                video.srcObject = null;
                stream = null;
            }
        }

        // Start camera when camera tab is shown
        document.getElementById('camera-tab').addEventListener('shown.bs.tab', function (e) {
            startCamera();
        });

        // Stop camera when upload tab is shown
        document.getElementById('upload-tab').addEventListener('shown.bs.tab', function (e) {
            stopCamera();
        });

        // Initialize camera on page load
        document.addEventListener('DOMContentLoaded', function() {
            startCamera();
        });

        // Capture the image when the camera form is submitted
        cameraForm.addEventListener('submit', (event) => {
            event.preventDefault();
            
            // Validate form if new employee
            if (document.getElementById('newEmployee').checked) {
                const form = document.getElementById('employeeForm');
                if (!form.checkValidity()) {
                    form.reportValidity();
                    return;
                }
            }
            
            // Collect form data
            if (!collectFormData()) {
                return;
            }
            
            captureImage();
            // Submit the form programmatically
            cameraForm.submit();
        });

        // Function to capture image from camera
        function captureImage() {
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataURL = canvas.toDataURL('image/jpeg');
            imageDataInput.value = dataURL;

            // Show the captured image preview
            imagePreview.src = dataURL;
            imagePreview.style.display = 'block';
        }
        
        // Add keyboard listener for spacebar and q
        document.addEventListener('keydown', (event) => {
            // Only work when camera tab is active
            if (!document.getElementById('camera').classList.contains('active')) return;
            
            if (event.code === 'Space') {
                // Capture on spacebar
                captureImage();
            } else if (event.code === 'KeyQ') {
                // Stop video stream on 'q'
                stopCamera();
            }
        });

        // File upload preview
        const photoInput = document.getElementById('photoFile');
        const uploadPreview = document.getElementById('uploadPreview');
        const uploadButton = document.getElementById('uploadButton');
        const uploadForm = document.getElementById('uploadForm');

        photoInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    uploadPreview.src = e.target.result;
                    uploadPreview.style.display = 'block';
                    uploadButton.disabled = false;
                }
                reader.readAsDataURL(file);
            } else {
                uploadPreview.style.display = 'none';
                uploadButton.disabled = true;
            }
        });

        // Submit handler for upload form
        uploadForm.addEventListener('submit', (event) => {
            event.preventDefault();
            
            // Validate form if new employee
            if (document.getElementById('newEmployee').checked) {
                const form = document.getElementById('employeeForm');
                if (!form.checkValidity()) {
                    form.reportValidity();
                    return;
                }
            }
            
            // Collect form data
            if (!collectFormData()) {
                return;
            }
            
            // Submit the form programmatically
            uploadForm.submit();
        });

        // Enable drag and drop for file upload
        const dropZone = document.querySelector('.custom-file-upload');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            dropZone.style.backgroundColor = 'rgba(78, 205, 196, 0.2)';
            dropZone.style.borderColor = 'var(--accent-color)';
        }

        function unhighlight() {
            dropZone.style.backgroundColor = 'rgba(78, 205, 196, 0.05)';
            dropZone.style.borderColor = 'var(--accent-color)';
        }

        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            photoInput.files = files;
            
            // Trigger change event manually
            const event = new Event('change');
            photoInput.dispatchEvent(event);
        }

        // Sync the instruction tabs with the main tabs
        document.getElementById('camera-tab').addEventListener('click', function() {
            document.getElementById('camera-instructions-tab').click();
        });

        document.getElementById('upload-tab').addEventListener('click', function() {
            document.getElementById('upload-instructions-tab').click();
        });
        
        // Set today's date as default for date hired
        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('date_hired').value = today;
        });