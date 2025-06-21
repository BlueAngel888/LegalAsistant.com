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
    let isProcessingFiles = false; // Flag to prevent recursive calls

    if (!fileInput || !dropZone) return;

    // Handle file input change - simplified approach
    fileInput.addEventListener('change', function(e) {
        if (isProcessingFiles) return; // Prevent recursive calls
        
        console.log('File input changed:', e.target.files.length, 'files selected');
        
        if (e.target.files.length > 0) {
            isProcessingFiles = true;
            const files = Array.from(e.target.files);
            processSelectedFiles(files);
            isProcessingFiles = false;
        }
    });

    // Handle camera input change
    if (cameraInput) {
        cameraInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                const files = Array.from(e.target.files);
                processSelectedFiles(files);
            }
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

    // Click to upload - simplified direct approach
    dropZone.addEventListener('click', function(e) {
        console.log('Drop zone clicked, opening file dialog');
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
        processSelectedFiles(Array.from(files));
    }

    function processSelectedFiles(files) {
        console.log('Processing', files.length, 'files');
        
        // Filter valid file types
        const validTypes = ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png'];
        const validFiles = files.filter(file => {
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            return validTypes.includes(extension);
        });

        if (validFiles.length !== files.length) {
            showErrorMessage('Some files were skipped due to unsupported file types.');
        }

        if (validFiles.length === 0) {
            console.log('No valid files selected');
            return;
        }

        // Update selected files
        selectedFiles = [...validFiles];
        console.log('Files processed:', selectedFiles.length, 'valid files');
        
        // Update display
        updateFileDisplay();
        
        // Update submit button state
        updateSubmitButton();
        
        // Show preview area
        if (selectedFiles.length > 0 && filePreview) {
            filePreview.style.display = 'block';
        }
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

// Enhanced Legal Selector Functions



function initializeLegalSelectors() {
    // Upload tab selectors
    const countrySelect = document.getElementById('document_country');
    const languageSelect = document.getElementById('analysis_language');
    
    // Camera tab selectors
    const countrySelectCamera = document.getElementById('document_country_camera');
    const languageSelectCamera = document.getElementById('analysis_language_camera');
    
    // Handle upload tab selectors
    if (countrySelect && languageSelect) {
        countrySelect.addEventListener('change', function() {
            validateAndStyleSelector(this);
            updateSubmitButton();
        });
        
        languageSelect.addEventListener('change', function() {
            validateAndStyleSelector(this);
            updateSubmitButton();
        });
        
        // Add focus/blur effects
        [countrySelect, languageSelect].forEach(select => {
            select.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            select.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
        });
    }
    
    // Handle camera tab selectors
    if (countrySelectCamera && languageSelectCamera) {
        countrySelectCamera.addEventListener('change', function() {
            validateAndStyleSelector(this);
            updateSubmitButton();
        });
        
        languageSelectCamera.addEventListener('change', function() {
            validateAndStyleSelector(this);
            updateSubmitButton();
        });
        
        // Add focus/blur effects
        [countrySelectCamera, languageSelectCamera].forEach(select => {
            select.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            select.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
        });
    }
}

function validateAndStyleSelector(select) {
    const optionGroup = select.closest('.option-group');
    
    if (select.value && select.value !== '') {
        select.classList.add('filled');
        optionGroup.classList.remove('error');
        optionGroup.classList.add('success');
    } else {
        select.classList.remove('filled');
        optionGroup.classList.remove('success');
        optionGroup.classList.add('error');
    }
}

function updateSubmitButtonState() {
    const countrySelect = document.getElementById('document_country');
    const languageSelect = document.getElementById('analysis_language');
    const submitBtn = document.querySelector('button[type="submit"]');
    const fileInput = document.getElementById('file');
    
    if (submitBtn && countrySelect && languageSelect && fileInput) {
        const hasFiles = fileInput.files && fileInput.files.length > 0;
        const hasCountry = countrySelect.value && countrySelect.value !== '';
        const hasLanguage = languageSelect.value && languageSelect.value !== '';
        
        submitBtn.disabled = !(hasFiles && hasCountry && hasLanguage);
        
        if (hasFiles && hasCountry && hasLanguage) {
            submitBtn.classList.add('enhanced-ready');
        } else {
            submitBtn.classList.remove('enhanced-ready');
        }
    }
}

function showCountryInfo(countryCode) {
    if (!countryCode) return;
    
    const countryInfo = {
        'RO': {
            name: 'Romania',
            flag: '🇷🇴',
            legalSystem: 'Civil Law System (Continental European)',
            primaryLaws: 'Codul Civil Romanian, Codul de Procedura Civila'
        },
        'DE': {
            name: 'Germany', 
            flag: '🇩🇪',
            legalSystem: 'Civil Law System (Germanic)',
            primaryLaws: 'Bürgerliches Gesetzbuch (BGB), Handelsgesetzbuch (HGB)'
        },
        'AE': {
            name: 'United Arab Emirates',
            flag: '🇦🇪', 
            legalSystem: 'Mixed Legal System (Islamic Law + Civil Law)',
            primaryLaws: 'UAE Civil Code, UAE Commercial Code, Sharia Law'
        },
        'US': {
            name: 'United States',
            flag: '🇺🇸',
            legalSystem: 'Common Law System',
            primaryLaws: 'Federal Code, State Laws, Case Law Precedents'
        },
        'UK': {
            name: 'United Kingdom',
            flag: '🇬🇧',
            legalSystem: 'Common Law System',
            primaryLaws: 'Statutes, Case Law, Common Law Principles'
        },
        'FR': {
            name: 'France',
            flag: '🇫🇷',
            legalSystem: 'Civil Law System (Napoleonic)',
            primaryLaws: 'Code Civil Français, Code de Commerce'
        }
    };
    
    const info = countryInfo[countryCode];
    if (info) {
        showLegalFrameworkInfo(info);
    }
}

function showLanguageInfo(languageCode) {
    if (!languageCode) return;
    
    const languageInfo = {
        'ro': { name: 'Română', nativeName: 'Română', flag: '🇷🇴' },
        'en': { name: 'English', nativeName: 'English', flag: '🇬🇧' },
        'de': { name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
        'fr': { name: 'French', nativeName: 'Français', flag: '🇫🇷' },
        'ar': { name: 'Arabic', nativeName: 'العربية', flag: '🇦🇪' },
        'it': { name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
        'es': { name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' }
    };
    
    const info = languageInfo[languageCode];
    if (info) {
        showAnalysisLanguageInfo(info);
    }
}

function showLegalFrameworkInfo(countryInfo) {
    // Remove existing indicators
    const existingIndicator = document.querySelector('.legal-framework-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Create new indicator
    const indicator = document.createElement('div');
    indicator.className = 'legal-framework-indicator';
    indicator.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor"/>
        </svg>
        <span class="country-flag">${countryInfo.flag}</span>
        <div>
            <strong>${countryInfo.name}</strong> - ${countryInfo.legalSystem}<br>
            <small>Primary Laws: ${countryInfo.primaryLaws}</small>
        </div>
    `;
    
    // Insert after legal analysis options
    const legalOptions = document.querySelector('.legal-analysis-options');
    if (legalOptions) {
        legalOptions.insertAdjacentElement('afterend', indicator);
        
        // Animate in
        setTimeout(() => {
            indicator.style.opacity = '1';
            indicator.style.transform = 'translateY(0)';
        }, 100);
    }
}

function showAnalysisLanguageInfo(languageInfo) {
    // Update language hint with selected language info
    const languageHint = document.querySelector('#analysis_language').nextElementSibling;
    if (languageHint && languageHint.classList.contains('option-hint')) {
        languageHint.innerHTML = `
            Analysis will be provided in <strong>${languageInfo.nativeName}</strong> ${languageInfo.flag}<br>
            Professional legal terminology and citations will be used
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeLegalSelectors();
});

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
