// Legal Assistant - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive elements
    initializeFileUpload();
    initializeFormValidation();
    initializeTooltips();
    initializeScrollEffects();
});

// Modern File Upload Functionality
function initializeFileUpload() {
    const fileInput = document.getElementById('file');
    const cameraInput = document.getElementById('cameraInput');
    const dropZone = document.getElementById('dropZone');
    const filePreview = document.getElementById('filePreview');
    const fileList = document.getElementById('fileList');
    const clearFilesBtn = document.getElementById('clearFiles');
    
    let selectedFiles = [];

    if (!fileInput || !dropZone) return;

    // Handle file input change
    fileInput.addEventListener('change', function(e) {
        handleFileSelection(Array.from(e.target.files));
    });

    // Handle camera input change
    if (cameraInput) {
        cameraInput.addEventListener('change', function(e) {
            handleFileSelection(Array.from(e.target.files));
        });
    }

    // Modern drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    dropZone.addEventListener('drop', handleDrop, false);

    // Click to upload
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Clear files functionality
    if (clearFilesBtn) {
        clearFilesBtn.addEventListener('click', clearAllFiles);
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropZone.classList.add('dragover');
    }

    function unhighlight() {
        dropZone.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFileSelection(Array.from(files));
    }

    function handleFileSelection(files) {
        // Filter valid file types
        const validTypes = ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png'];
        const validFiles = files.filter(file => {
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            return validTypes.includes(extension);
        });

        if (validFiles.length !== files.length) {
            showErrorMessage('Some files were skipped due to unsupported file types.');
        }

        // Add new files to selection
        selectedFiles = [...selectedFiles, ...validFiles];
        
        // Update file input
        updateFileInputValue();
        
        // Update display
        updateFileDisplay();
        
        // Show preview area
        if (selectedFiles.length > 0) {
            filePreview.style.display = 'block';
        }
    }

    function updateFileInputValue() {
        // Create a new DataTransfer object to update the file input
        const dt = new DataTransfer();
        selectedFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
    }

    function updateFileDisplay() {
        if (!fileList) return;
        
        fileList.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = createFileItem(file, index);
            fileList.appendChild(fileItem);
        });
        
        // Update submit button state
        updateSubmitButton();
    }

    function updateSubmitButton() {
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = selectedFiles.length === 0;
        }
    }

    function createFileItem(file, index) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const fileExtension = file.name.split('.').pop().toUpperCase();
        const fileSize = formatFileSize(file.size);
        
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-icon">${fileExtension}</div>
                <div class="file-details">
                    <h5>${file.name}</h5>
                    <small>${fileSize}</small>
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(${index})">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        `;
        
        return fileItem;
    }

    function clearAllFiles() {
        selectedFiles = [];
        fileInput.value = '';
        filePreview.style.display = 'none';
        updateFileDisplay();
        updateSubmitButton();
    }

    // Make removeFile function global
    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateFileInputValue();
        updateFileDisplay();
        
        if (selectedFiles.length === 0) {
            filePreview.style.display = 'none';
        }
    };
}

    function updateFileDisplay(files) {
        if (!fileList || !selectedFiles || !submitBtn) return;

        if (files.length > 0) {
            fileList.style.display = 'block';
            selectedFiles.innerHTML = '';
            
            let totalSize = 0;
            let validFiles = 0;
            
            files.forEach(file => {
                totalSize += file.size;
                
                // Check file size (16MB limit)
                const isValidSize = file.size <= 16 * 1024 * 1024;
                
                // Check file type
                const allowedTypes = ['pdf', 'docx', 'doc', 'txt', 'jpg', 'jpeg', 'png'];
                const fileExtension = file.name.split('.').pop().toLowerCase();
                const isValidType = allowedTypes.includes(fileExtension);
                
                if (isValidSize && isValidType) {
                    validFiles++;
                }
                
                const li = document.createElement('li');
                li.className = `list-group-item d-flex justify-content-between align-items-center ${
                    !isValidSize || !isValidType ? 'list-group-item-danger' : ''
                }`;
                
                let statusIcon = '<i class="fas fa-check-circle text-success"></i>';
                let statusText = '';
                
                if (!isValidSize) {
                    statusIcon = '<i class="fas fa-exclamation-triangle text-warning"></i>';
                    statusText = ' (Too large)';
                } else if (!isValidType) {
                    statusIcon = '<i class="fas fa-exclamation-triangle text-warning"></i>';
                    statusText = ' (Unsupported format)';
                }
                
                li.innerHTML = `
                    <span>
                        <i class="fas fa-file me-2"></i>${file.name}${statusText}
                    </span>
                    <span class="d-flex align-items-center">
                        <span class="badge bg-secondary rounded-pill me-2">${formatFileSize(file.size)}</span>
                        ${statusIcon}
                    </span>
                `;
                selectedFiles.appendChild(li);
            });
            
            // Enable/disable submit button based on valid files
            submitBtn.disabled = validFiles === 0;
            
            // Show total size if multiple files
            if (files.length > 1) {
                const totalLi = document.createElement('li');
                totalLi.className = 'list-group-item bg-light';
                totalLi.innerHTML = `
                    <strong>Total: ${files.length} files (${formatFileSize(totalSize)})</strong>
                `;
                selectedFiles.appendChild(totalLi);
            }
        } else {
            fileList.style.display = 'none';
            submitBtn.disabled = true;
        }
    }
}

// Basic file upload - no complex mobile handling

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            
            if (submitButton && !submitButton.disabled) {
                // Add loading state
                const originalText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.classList.add('loading');
                
                // Update button text based on form action
                if (form.action.includes('upload')) {
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing files...';
                } else if (form.action.includes('checkout')) {
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Redirecting to payment...';
                }
                
                // Reset button after a timeout (fallback)
                setTimeout(() => {
                    if (submitButton.disabled) {
                        submitButton.disabled = false;
                        submitButton.classList.remove('loading');
                        submitButton.innerHTML = originalText;
                    }
                }, 10000);
            }
        });
    });
}

// Initialize Bootstrap Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Scroll Effects
function initializeScrollEffects() {
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }
        });
    }
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Copy to Clipboard Functionality
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "absolute";
        textArea.style.left = "-999999px";
        
        document.body.prepend(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
        } catch (error) {
            console.error('Copy failed:', error);
        } finally {
            textArea.remove();
        }
    }
}

// Show Success Message
function showSuccessMessage(message, duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Show Error Message
function showErrorMessage(message, duration = 8000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Smooth Scroll to Element
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Loading Overlay Functions
function showLoadingOverlay(message = 'Processing...') {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'd-flex justify-content-center align-items-center position-fixed w-100 h-100';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    overlay.style.zIndex = '10000';
    
    overlay.innerHTML = `
        <div class="card border-0 shadow-lg">
            <div class="card-body text-center p-4">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h5 class="mb-0">${message}</h5>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Export functions for global use
window.LegalAssistant = {
    formatFileSize,
    copyToClipboard,
    showSuccessMessage,
    showErrorMessage,
    smoothScrollTo,
    showLoadingOverlay,
    hideLoadingOverlay
};
