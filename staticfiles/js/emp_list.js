        // Modal functionality
        const modal = document.getElementById("searchModal");
        const btn = document.getElementById("searchByImageBtn");
        const span = document.getElementsByClassName("close-modal")[0];
        const uploadArea = document.getElementById("uploadArea");
        const fileInput = document.getElementById("imageFile");
        
        // Open modal
        btn.onclick = function() {
            modal.style.display = "block";
        }
        
        // Close modal
        span.onclick = function() {
            modal.style.display = "none";
        }
        
        // Close modal if clicked outside
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }
        
        // Upload area functionality
        uploadArea.onclick = function() {
            fileInput.click();
        }
        
        // Display file name when selected
        fileInput.onchange = function() {
            if (fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name;
                document.querySelector(".upload-text").textContent = "Selected: " + fileName;
            }
        }
        
        // Drag and drop functionality
        uploadArea.addEventListener("dragover", function(e) {
            e.preventDefault();
            uploadArea.style.backgroundColor = "rgba(78, 205, 196, 0.2)";
        });
        
        uploadArea.addEventListener("dragleave", function(e) {
            e.preventDefault();
            uploadArea.style.backgroundColor = "transparent";
        });
        
        uploadArea.addEventListener("drop", function(e) {
            e.preventDefault();
            uploadArea.style.backgroundColor = "transparent";
            
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                const fileName = e.dataTransfer.files[0].name;
                document.querySelector(".upload-text").textContent = "Selected: " + fileName;
            }
        });
    