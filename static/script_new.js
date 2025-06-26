// OCR Upload and Processing JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const processing = document.getElementById('processing');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const extractedText = document.getElementById('extracted-text');
    const fileInfo = document.getElementById('file-info');
    const newUploadBtn = document.getElementById('new-upload-btn');

    // Click to browse files
    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // New upload button
    newUploadBtn.addEventListener('click', resetUpload);

    function handleDragOver(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    }

    function handleDrop(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            processFile(file);
        }
    }

    function processFile(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            showError('Please select a valid image file.');
            return;
        }

        // Validate file size (10MB limit)
        const maxSize = 10 * 1024 * 1024; // 10MB in bytes
        if (file.size > maxSize) {
            showError('File size must be less than 10MB.');
            return;
        }

        // Hide any previous results/errors
        hideAllSections();
        
        // Show processing
        processing.style.display = 'block';
        
        // Create FormData and send to OCR endpoint
        const formData = new FormData();
        formData.append('image', file);

        fetch('/api/ocr', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            processing.style.display = 'none';
            
            if (data.success) {
                showResults(data, file);
            } else {
                showError(data.error || 'Processing failed. Please try again.');
            }
        })
        .catch(err => {
            processing.style.display = 'none';
            console.error('OCR processing error:', err);
            showError('Network error. Please check your connection and try again.');
        });
    }

    function showResults(data, file) {
        // Update file info
        fileInfo.innerHTML = `
            <strong>File:</strong> ${data.filename} | 
            <strong>Size:</strong> ${formatFileSize(file.size)} | 
            <strong>Dimensions:</strong> ${data.image_size} |
            <strong>Characters extracted:</strong> ${data.text.length}
        `;

        // Update extracted text
        extractedText.textContent = data.text;

        // Show results section
        results.style.display = 'block';
        
        // Scroll to results
        results.scrollIntoView({ behavior: 'smooth' });
    }

    function showError(message) {
        error.textContent = message;
        error.style.display = 'block';
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            error.style.display = 'none';
        }, 5000);
    }

    function hideAllSections() {
        processing.style.display = 'none';
        results.style.display = 'none';
        error.style.display = 'none';
    }

    function resetUpload() {
        fileInput.value = '';
        hideAllSections();
        uploadArea.style.display = 'block';
        
        // Scroll back to upload area
        uploadArea.scrollIntoView({ behavior: 'smooth' });
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
});