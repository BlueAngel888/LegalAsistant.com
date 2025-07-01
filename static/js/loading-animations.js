// Legal-themed Loading Animation System

class LegalLoadingManager {
    constructor() {
        this.currentLoader = null;
        this.progressTimer = null;
        this.statusTimer = null;
        this.init();
    }

    init() {
        // Create loading overlay if it doesn't exist
        if (!document.getElementById('loading-overlay')) {
            this.createLoadingOverlay();
        }
    }

    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-container">
                <div id="loading-animation-container">
                    <!-- Animation will be inserted here -->
                </div>
                <div class="loading-text" id="loading-text">Processing Document...</div>
                <div class="loading-subtext" id="loading-subtext">Please wait while we analyze your legal document</div>
                <div class="progress-steps">
                    <div class="progress-step" id="step-upload">
                        <span class="step-label">Upload</span>
                    </div>
                    <div class="progress-step" id="step-process">
                        <span class="step-label">Process</span>
                    </div>
                    <div class="progress-step" id="step-analyze">
                        <span class="step-label">Analyze</span>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    showLoader(type = 'document', options = {}) {
        const overlay = document.getElementById('loading-overlay');
        const animationContainer = document.getElementById('loading-animation-container');
        const textElement = document.getElementById('loading-text');
        const subtextElement = document.getElementById('loading-subtext');

        // Clear any existing timers
        this.clearTimers();

        // Set animation type
        animationContainer.innerHTML = this.getAnimationHTML(type);

        // Set text content
        textElement.textContent = options.title || this.getDefaultTitle(type);
        subtextElement.textContent = options.subtitle || this.getDefaultSubtitle(type);

        // Show overlay
        overlay.classList.add('active');

        // Start progress animation
        this.startProgressAnimation(options.duration || 8000);

        // Start status updates
        this.startStatusUpdates();

        this.currentLoader = type;
    }

    hideLoader() {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.remove('active');
        this.clearTimers();
        this.currentLoader = null;
    }

    getAnimationHTML(type) {
        switch (type) {
            case 'scale':
                return `
                    <div class="legal-scale">
                        <div class="scale-base"></div>
                        <div class="scale-beam">
                            <div class="scale-chain left"></div>
                            <div class="scale-chain right"></div>
                            <div class="scale-pan left"></div>
                            <div class="scale-pan right"></div>
                        </div>
                    </div>
                `;
            case 'gavel':
                return `
                    <div class="gavel-animation">
                        <div class="gavel">
                            <div class="gavel-handle"></div>
                        </div>
                        <div class="gavel-block"></div>
                        <div class="gavel-impact"></div>
                    </div>
                `;
            case 'document':
            default:
                return `
                    <div class="document-animation">
                        <div class="document-stack">
                            <div class="document-page">
                                <div class="document-lines"></div>
                            </div>
                            <div class="document-page">
                                <div class="document-lines"></div>
                            </div>
                            <div class="document-page">
                                <div class="document-lines"></div>
                            </div>
                        </div>
                    </div>
                `;
        }
    }

    getDefaultTitle(type) {
        switch (type) {
            case 'scale':
                return 'Weighing Legal Evidence...';
            case 'gavel':
                return 'Rendering Judgment...';
            case 'document':
            default:
                return 'Processing Document...';
        }
    }

    getDefaultSubtitle(type) {
        switch (type) {
            case 'scale':
                return 'Analyzing legal implications and balancing arguments';
            case 'gavel':
                return 'Finalizing legal analysis and recommendations';
            case 'document':
            default:
                return 'Please wait while we analyze your legal document';
        }
    }

    startProgressAnimation(duration) {
        const progressBar = document.getElementById('loading-progress-bar');
        let progress = 0;
        const increment = 100 / (duration / 100);

        this.progressTimer = setInterval(() => {
            progress += increment;
            if (progress >= 100) {
                progress = 100;
                clearInterval(this.progressTimer);
            }
            progressBar.style.width = `${progress}%`;
        }, 100);
    }

    startStatusUpdates() {
        const progressSteps = [
            document.getElementById('step-upload'),
            document.getElementById('step-process'),
            document.getElementById('step-analyze')
        ];

        let currentStep = 0;
        
        // Activate first step immediately
        progressSteps[0].classList.add('active');

        this.statusTimer = setInterval(() => {
            if (currentStep < progressSteps.length - 1) {
                // Complete current step
                progressSteps[currentStep].classList.remove('active');
                progressSteps[currentStep].classList.add('completed');
                
                // Move to next step
                currentStep++;
                progressSteps[currentStep].classList.add('active');
            }
        }, 3000); // 3 seconds per step
    }

    clearTimers() {
        if (this.progressTimer) {
            clearInterval(this.progressTimer);
            this.progressTimer = null;
        }
        if (this.statusTimer) {
            clearInterval(this.statusTimer);
            this.statusTimer = null;
        }
    }

    // Predefined loading scenarios
    showDocumentUpload() {
        this.showLoader('document', {
            title: 'Uploading Document...',
            subtitle: 'Securely processing your legal files',
            duration: 3000
        });
    }

    showDocumentAnalysis() {
        this.showLoader('scale', {
            title: 'Analyzing Legal Document...',
            subtitle: 'AI is reviewing content and legal implications',
            duration: 8000
        });
    }

    showPaymentProcessing() {
        this.showLoader('gavel', {
            title: 'Processing Payment...',
            subtitle: 'Securing your transaction and preparing analysis',
            duration: 5000
        });
    }

    showContractGeneration() {
        this.showLoader('document', {
            title: 'Generating Contract...',
            subtitle: 'Creating legal document based on your specifications',
            duration: 6000
        });
    }

    showLegalResearch() {
        this.showLoader('scale', {
            title: 'Researching Legal Framework...',
            subtitle: 'Analyzing applicable laws and regulations',
            duration: 7000
        });
    }
}

// Global instance
const legalLoader = new LegalLoadingManager();

// Integration with existing form submissions
document.addEventListener('DOMContentLoaded', function() {
    // Override existing upload functionality
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            // Don't prevent default, just show loader
            legalLoader.showDocumentUpload();
        });
    }

    // Override checkout form
    const checkoutForm = document.querySelector('form[action*="checkout"]');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            legalLoader.showPaymentProcessing();
        });
    }

    // Override free access form
    const freeAccessForm = document.querySelector('form[action*="free-access"]');
    if (freeAccessForm) {
        freeAccessForm.addEventListener('submit', function(e) {
            legalLoader.showDocumentAnalysis();
        });
    }

    // Legal services forms
    const contractForm = document.querySelector('form[action*="generate-contract"]');
    if (contractForm) {
        contractForm.addEventListener('submit', function(e) {
            legalLoader.showContractGeneration();
        });
    }

    const legalRequestForm = document.querySelector('form[action*="generate-legal-request"]');
    if (legalRequestForm) {
        legalRequestForm.addEventListener('submit', function(e) {
            legalLoader.showLegalResearch();
        });
    }

    const penaltyForm = document.querySelector('form[action*="analyze-penalty"]');
    if (penaltyForm) {
        penaltyForm.addEventListener('submit', function(e) {
            legalLoader.showDocumentAnalysis();
        });
    }

    const realEstateForm = document.querySelector('form[action*="verify-real-estate"]');
    if (realEstateForm) {
        realEstateForm.addEventListener('submit', function(e) {
            legalLoader.showLegalResearch();
        });
    }

    // Hide loader when page fully loads (for redirects)
    window.addEventListener('load', function() {
        // Small delay to ensure smooth transition
        setTimeout(() => {
            legalLoader.hideLoader();
        }, 500);
    });

    // Hide loader if user navigates away
    window.addEventListener('beforeunload', function() {
        legalLoader.hideLoader();
    });
});

// Export for external use
window.legalLoader = legalLoader;