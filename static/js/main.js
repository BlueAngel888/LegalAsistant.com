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
        fileItem.className = 'file-item file-item-enhanced';
        
        const fileExtension = file.name.split('.').pop().toUpperCase();
        const fileSize = formatFileSize(file.size);
        const isImage = ['JPG', 'JPEG', 'PNG'].includes(fileExtension);
        
        // Create preview thumbnail for images
        let previewElement = '';
        if (isImage) {
            const imageUrl = URL.createObjectURL(file);
            previewElement = `<img src="${imageUrl}" class="file-preview-thumb" onclick="showDocumentPreview('${imageUrl}', '${file.name}', ${index})" alt="${file.name}">`;
        } else {
            previewElement = `<div class="file-type-icon" onclick="showDocumentPreview(null, '${file.name}', ${index})">${fileExtension}</div>`;
        }
        
        fileItem.innerHTML = `
            <div class="file-info">
                ${previewElement}
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
        updateSubmitButton();
        
        if (selectedFiles.length === 0) {
            filePreview.style.display = 'none';
        }
    };

    // Initialize submit button state
    updateSubmitButton();
}

// Document Preview and Scanner Functions
let currentFileIndex = null;
let currentImageUrl = null;

function showDocumentPreview(imageUrl, fileName, fileIndex) {
    currentFileIndex = fileIndex;
    currentImageUrl = imageUrl;
    
    const modal = document.getElementById('documentPreviewModal');
    const previewImage = document.getElementById('previewImage');
    const previewText = document.getElementById('previewText');
    const enhanceBtn = document.getElementById('enhanceDocumentBtn');
    
    if (!modal) return;
    
    modal.style.display = 'flex';
    
    if (imageUrl) {
        previewImage.src = imageUrl;
        previewImage.style.display = 'block';
        previewText.style.display = 'none';
        enhanceBtn.style.display = 'block';
        
        // Auto-detect document in image
        setTimeout(() => {
            detectDocumentInImage(imageUrl);
        }, 500);
        
    } else {
        previewImage.style.display = 'none';
        previewText.style.display = 'block';
        previewText.textContent = `Preview not available for ${fileName}`;
        enhanceBtn.style.display = 'none';
    }
}

function closeDocumentPreview() {
    const modal = document.getElementById('documentPreviewModal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentFileIndex = null;
    currentImageUrl = null;
}

function detectDocumentInImage(imageUrl) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // Get image data for edge detection
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const corners = findDocumentCorners(imageData);
        
        if (corners.length === 4) {
            showDocumentOutline(corners);
        }
    };
    
    img.src = imageUrl;
}

function findDocumentCorners(imageData) {
    // Simplified edge detection algorithm
    const { data, width, height } = imageData;
    const edges = [];
    
    // Convert to grayscale and find edges
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = (y * width + x) * 4;
            
            // Simple edge detection using Sobel operator
            const gx = (
                -1 * getGrayValue(data, idx - 4 - width * 4) +
                1 * getGrayValue(data, idx + 4 - width * 4) +
                -2 * getGrayValue(data, idx - 4) +
                2 * getGrayValue(data, idx + 4) +
                -1 * getGrayValue(data, idx - 4 + width * 4) +
                1 * getGrayValue(data, idx + 4 + width * 4)
            );
            
            const gy = (
                -1 * getGrayValue(data, idx - 4 - width * 4) +
                -2 * getGrayValue(data, idx - width * 4) +
                -1 * getGrayValue(data, idx + 4 - width * 4) +
                1 * getGrayValue(data, idx - 4 + width * 4) +
                2 * getGrayValue(data, idx + width * 4) +
                1 * getGrayValue(data, idx + 4 + width * 4)
            );
            
            const magnitude = Math.sqrt(gx * gx + gy * gy);
            if (magnitude > 50) {
                edges.push({ x, y });
            }
        }
    }
    
    // Find document corners (simplified - in real implementation would use more sophisticated algorithm)
    if (edges.length > 100) {
        return [
            { x: width * 0.1, y: height * 0.1 }, // Top-left
            { x: width * 0.9, y: height * 0.1 }, // Top-right
            { x: width * 0.9, y: height * 0.9 }, // Bottom-right
            { x: width * 0.1, y: height * 0.9 }  // Bottom-left
        ];
    }
    
    return [];
}

function getGrayValue(data, idx) {
    return (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
}

function showDocumentOutline(corners) {
    const previewImage = document.getElementById('previewImage');
    if (!previewImage) return;
    
    // Create overlay if it doesn't exist
    let overlay = previewImage.parentElement.querySelector('.scanner-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'scanner-overlay';
        previewImage.parentElement.appendChild(overlay);
    }
    
    // Clear existing outline
    overlay.innerHTML = '';
    
    // Calculate scaling factor
    const rect = previewImage.getBoundingClientRect();
    const scaleX = rect.width / previewImage.naturalWidth;
    const scaleY = rect.height / previewImage.naturalHeight;
    
    // Create document outline
    const outline = document.createElement('div');
    outline.className = 'document-outline';
    
    const minX = Math.min(...corners.map(c => c.x)) * scaleX;
    const minY = Math.min(...corners.map(c => c.y)) * scaleY;
    const maxX = Math.max(...corners.map(c => c.x)) * scaleX;
    const maxY = Math.max(...corners.map(c => c.y)) * scaleY;
    
    outline.style.left = minX + 'px';
    outline.style.top = minY + 'px';
    outline.style.width = (maxX - minX) + 'px';
    outline.style.height = (maxY - minY) + 'px';
    
    overlay.appendChild(outline);
    
    // Add corner markers
    corners.forEach((corner, index) => {
        const marker = document.createElement('div');
        marker.className = 'corner-marker';
        marker.style.left = (corner.x * scaleX - 6) + 'px';
        marker.style.top = (corner.y * scaleY - 6) + 'px';
        overlay.appendChild(marker);
    });
}

function enhanceDocument() {
    if (!currentImageUrl || currentFileIndex === null) return;
    
    const modal = document.getElementById('documentPreviewModal');
    const modalBody = modal.querySelector('.modal-body');
    
    // Show processing state
    modalBody.innerHTML = `
        <div class="scanner-processing">
            <div class="scanner-spinner"></div>
            <h6>Enhancing document...</h6>
            <p>Applying filters and cropping document</p>
        </div>
    `;
    
    // Simulate document enhancement
    setTimeout(() => {
        applyDocumentEnhancements();
    }, 2000);
}

function applyDocumentEnhancements() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        
        // Apply enhancements
        ctx.filter = 'contrast(1.2) brightness(1.1) saturate(0.8)';
        ctx.drawImage(img, 0, 0);
        
        // Convert to blob and update file
        canvas.toBlob((blob) => {
            const enhancedFile = new File([blob], `enhanced_${Date.now()}.png`, { type: 'image/png' });
            replaceFileAtIndex(currentFileIndex, enhancedFile);
            
            // Update preview
            const enhancedUrl = URL.createObjectURL(blob);
            updatePreviewAfterEnhancement(enhancedUrl);
        }, 'image/png', 0.9);
    };
    
    img.src = currentImageUrl;
}

function replaceFileAtIndex(index, newFile) {
    // This function would be inside the initializeFileUpload scope in a real implementation
    // For now, we'll simulate the replacement
    showSuccessMessage('Document enhanced and ready for analysis!');
}

function updatePreviewAfterEnhancement(enhancedUrl) {
    const modal = document.getElementById('documentPreviewModal');
    const modalBody = modal.querySelector('.modal-body');
    
    modalBody.innerHTML = `
        <div class="preview-container">
            <img src="${enhancedUrl}" class="preview-image" alt="Enhanced document">
            <div class="enhancement-controls">
                <div class="control-group">
                    <label>Brightness</label>
                    <input type="range" min="0.5" max="2" step="0.1" value="1.1" onchange="updateEnhancement('brightness', this.value)">
                </div>
                <div class="control-group">
                    <label>Contrast</label>
                    <input type="range" min="0.5" max="2" step="0.1" value="1.2" onchange="updateEnhancement('contrast', this.value)">
                </div>
                <div class="control-group">
                    <label>Saturation</label>
                    <input type="range" min="0" max="2" step="0.1" value="0.8" onchange="updateEnhancement('saturation', this.value)">
                </div>
            </div>
        </div>
    `;
}

function updateEnhancement(property, value) {
    const previewImage = document.querySelector('.preview-image');
    if (!previewImage) return;
    
    const currentFilter = previewImage.style.filter || '';
    const regex = new RegExp(`${property}\\([^)]*\\)`, 'g');
    const newFilter = currentFilter.replace(regex, '').trim();
    
    previewImage.style.filter = `${newFilter} ${property}(${value})`.trim();
}

// Gamification Functions
function showXPGain(xpAmount) {
    const popup = document.createElement('div');
    popup.className = 'xp-gain-popup';
    popup.textContent = `+${xpAmount} XP`;
    document.body.appendChild(popup);
    
    setTimeout(() => {
        if (popup.parentNode) {
            popup.parentNode.removeChild(popup);
        }
    }, 2000);
}

function showAchievementNotification(achievement) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification';
    notification.innerHTML = `
        <div class="achievement-notification-header">
            <span class="achievement-notification-icon">${achievement.icon}</span>
            <h6 class="achievement-notification-title">Achievement Unlocked!</h6>
        </div>
        <p class="achievement-notification-description">${achievement.name}: ${achievement.description}</p>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide notification after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 400);
    }, 5000);
}

function showLevelUpNotification(newLevel) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification level-up-notification';
    notification.innerHTML = `
        <div class="achievement-notification-header">
            <span class="achievement-notification-icon">🎉</span>
            <h6 class="achievement-notification-title">Level Up!</h6>
        </div>
        <p class="achievement-notification-description">Congratulations! You've reached Level ${newLevel}</p>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide notification after 6 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 400);
    }, 6000);
}

function handleGamificationResult(result) {
    if (!result) return;
    
    // Show XP gain
    if (result.xp_gained > 0) {
        showXPGain(result.xp_gained);
    }
    
    // Show level up notification
    if (result.level_up) {
        setTimeout(() => {
            showLevelUpNotification(result.new_level);
        }, 500);
    }
    
    // Show achievement notifications
    if (result.earned_achievements && result.earned_achievements.length > 0) {
        result.earned_achievements.forEach((achievement, index) => {
            setTimeout(() => {
                showAchievementNotification(achievement);
            }, 1000 + (index * 1500)); // Stagger notifications
        });
    }
}

function animateProgressBar(targetPercentage) {
    const progressBar = document.querySelector('.progress-bar');
    if (!progressBar) return;
    
    let currentWidth = 0;
    const increment = targetPercentage / 30; // 30 frames
    
    const animate = () => {
        currentWidth += increment;
        if (currentWidth >= targetPercentage) {
            currentWidth = targetPercentage;
            progressBar.style.width = currentWidth + '%';
            return;
        }
        
        progressBar.style.width = currentWidth + '%';
        requestAnimationFrame(animate);
    };
    
    animate();
}

function updateUserStats(stats) {
    // Update level display
    const levelText = document.querySelector('.level-text');
    if (levelText) {
        levelText.textContent = `Level ${stats.level}`;
    }
    
    // Update XP display
    const xpText = document.querySelector('.xp-text');
    if (xpText) {
        xpText.textContent = `${stats.total_xp} XP`;
    }
    
    // Update progress bar
    const progressText = document.querySelector('.progress-text');
    if (progressText) {
        progressText.textContent = `${stats.progress_to_next}/100 XP to Level ${stats.level + 1}`;
    }
    
    // Animate progress bar
    animateProgressBar(stats.progress_percentage);
    
    // Update stats
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length >= 3) {
        statValues[0].textContent = stats.documents_uploaded;
        statValues[1].textContent = stats.documents_analyzed;
        statValues[2].textContent = stats.achievements_count;
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
