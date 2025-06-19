// Legal Assistant - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive elements
    initializeFileUpload();
    initializeFormValidation();
    initializeTooltips();
    initializeScrollEffects();
});

// File Upload Functionality
function initializeFileUpload() {
    const fileInput = document.getElementById('file');
    const fileList = document.getElementById('fileList');
    const selectedFiles = document.getElementById('selectedFiles');
    const submitBtn = document.getElementById('submitBtn');

    if (!fileInput) return;

    // Handle file selection display
    fileInput.addEventListener('change', function() {
        const files = Array.from(this.files);
        updateFileDisplay(files);
    });

    // Simple drag and drop for desktop only
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea && window.innerWidth >= 768) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('border-primary');
        });

        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('border-primary');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('border-primary');
            
            const files = e.dataTransfer.files;
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        });
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
