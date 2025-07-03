
<old_str>// Loading animations and progress tracking
class LegalLoadingAnimator {
    constructor() {
        this.currentStep = 0;
        this.progress = 0;
        this.steps = [
            { icon: '📄', label: 'Document Upload' },
            { icon: '🔍', label: 'Text Analysis' },
            { icon: '⚖️', label: 'Legal Review' },
            { icon: '✅', label: 'Complete' }
        ];
    }

    showLoading(message = 'Analyzing document...') {
        const loadingHtml = `
            <div class="loading-container">
                <div class="scales-container">
                    <div class="scales-base"></div>
                    <div class="scales-arm">
                        <div class="scales-pan left"></div>
                        <div class="scales-pan right"></div>
                    </div>
                </div>
                <div class="loading-text">${message}</div>
                <div class="loading-subtext">Please wait while we analyze your legal document...</div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>
                <div class="progress-text">0% Complete</div>
                <div class="analysis-steps">
                    ${this.steps.map((step, index) => `
                        <div class="step ${index === 0 ? 'active' : ''}" data-step="${index}">
                            <div class="step-icon">${step.icon}</div>
                            <div class="step-label">${step.label}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        return loadingHtml;
    }

    updateProgress(percentage, stepIndex = null) {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.querySelector('.progress-text');
        
        if (progressBar && progressText) {
            progressBar.style.width = percentage + '%';
            progressText.textContent = Math.round(percentage) + '% Complete';
        }

        if (stepIndex !== null) {
            this.updateStep(stepIndex);
        }
    }

    updateStep(stepIndex) {
        const steps = document.querySelectorAll('.step');
        
        steps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            
            if (index < stepIndex) {
                step.classList.add('completed');
            } else if (index === stepIndex) {
                step.classList.add('active');
            }
        });
    }

    simulateProgress(duration = 30000) {
        let startTime = Date.now();
        let currentProgress = 0;
        
        const interval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const progressPercentage = Math.min((elapsed / duration) * 100, 95);
            
            // Update step based on progress
            let stepIndex = 0;
            if (progressPercentage > 25) stepIndex = 1;
            if (progressPercentage > 50) stepIndex = 2;
            if (progressPercentage > 80) stepIndex = 3;
            
            this.updateProgress(progressPercentage, stepIndex);
            
            if (progressPercentage >= 95) {
                clearInterval(interval);
            }
        }, 500);
        
        return interval;
    }

    hideLoading() {
        const loadingContainer = document.querySelector('.loading-container');
        if (loadingContainer) {
            loadingContainer.style.opacity = '0';
            setTimeout(() => {
                if (loadingContainer.parentNode) {
                    loadingContainer.parentNode.removeChild(loadingContainer);
                }
            }, 300);
        }
    }
}

// Global instance
window.legalLoader = new LegalLoadingAnimator();</old_str>
<new_str>// Enhanced Loading animations with detailed legal analysis steps
class LegalLoadingAnimator {
    constructor() {
        this.currentStep = 0;
        this.progress = 0;
        this.steps = [
            { icon: '📄', label: 'Document Processing' },
            { icon: '🔍', label: 'Text Extraction' },
            { icon: '🌍', label: 'Country Laws' },
            { icon: '⚖️', label: 'Legal Analysis' },
            { icon: '🔬', label: 'Nullity Check' },
            { icon: '✅', label: 'Complete Analysis' }
        ];
        this.currentInterval = null;
    }

    showLoading(message = 'Analyzing legal document with AI...') {
        const loadingHtml = `
            <div class="loading-container">
                <div class="scales-container">
                    <div class="scales-base"></div>
                    <div class="scales-fulcrum"></div>
                    <div class="scales-arm">
                        <div class="scales-chain left"></div>
                        <div class="scales-chain right"></div>
                        <div class="scales-pan left">
                            <div class="scales-evidence"></div>
                        </div>
                        <div class="scales-pan right">
                            <div class="scales-evidence"></div>
                        </div>
                    </div>
                </div>
                <div class="loading-text">${message}</div>
                <div class="loading-subtext">Analyzing document according to country-specific laws...<br>Checking for legal nullity and fraudulent clauses...</div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>
                <div class="progress-text">0% Complete</div>
                <div class="analysis-steps">
                    ${this.steps.map((step, index) => `
                        <div class="step ${index === 0 ? 'active' : ''}" data-step="${index}">
                            <div class="step-icon">${step.icon}</div>
                            <div class="step-label">${step.label}</div>
                        </div>
                    `).join('')}
                </div>
                <div class="legal-status">
                    <strong>Status:</strong> <span id="current-status">Initializing legal analysis...</span>
                </div>
            </div>
        `;
        
        return loadingHtml;
    }

    updateProgress(percentage, stepIndex = null, statusMessage = null) {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.querySelector('.progress-text');
        const statusElement = document.getElementById('current-status');
        
        if (progressBar && progressText) {
            progressBar.style.width = percentage + '%';
            progressText.textContent = Math.round(percentage) + '% Complete';
        }

        if (stepIndex !== null) {
            this.updateStep(stepIndex);
        }

        if (statusMessage && statusElement) {
            statusElement.textContent = statusMessage;
        }
    }

    updateStep(stepIndex) {
        const steps = document.querySelectorAll('.step');
        
        steps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            
            if (index < stepIndex) {
                step.classList.add('completed');
            } else if (index === stepIndex) {
                step.classList.add('active');
            }
        });
    }

    simulateProgress(duration = 45000) {
        if (this.currentInterval) {
            clearInterval(this.currentInterval);
        }

        let startTime = Date.now();
        const statusMessages = [
            'Extracting text from documents...',
            'Identifying document type and parties...',
            'Loading country-specific legal framework...',
            'Performing comprehensive legal analysis...',
            'Checking for legal nullity and procedural defects...',
            'Finalizing detailed legal assessment...'
        ];
        
        this.currentInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const progressPercentage = Math.min((elapsed / duration) * 100, 95);
            
            // Update step and status based on progress
            let stepIndex = 0;
            let statusMessage = statusMessages[0];
            
            if (progressPercentage > 15) {
                stepIndex = 1;
                statusMessage = statusMessages[1];
            }
            if (progressPercentage > 30) {
                stepIndex = 2;
                statusMessage = statusMessages[2];
            }
            if (progressPercentage > 50) {
                stepIndex = 3;
                statusMessage = statusMessages[3];
            }
            if (progressPercentage > 75) {
                stepIndex = 4;
                statusMessage = statusMessages[4];
            }
            if (progressPercentage > 90) {
                stepIndex = 5;
                statusMessage = statusMessages[5];
            }
            
            this.updateProgress(progressPercentage, stepIndex, statusMessage);
            
            if (progressPercentage >= 95) {
                clearInterval(this.currentInterval);
                this.currentInterval = null;
            }
        }, 800);
        
        return this.currentInterval;
    }

    completeProgress() {
        if (this.currentInterval) {
            clearInterval(this.currentInterval);
            this.currentInterval = null;
        }
        
        this.updateProgress(100, 5, 'Legal analysis completed successfully!');
        
        // Complete all steps
        const steps = document.querySelectorAll('.step');
        steps.forEach(step => {
            step.classList.remove('active');
            step.classList.add('completed');
        });
    }

    hideLoading() {
        if (this.currentInterval) {
            clearInterval(this.currentInterval);
            this.currentInterval = null;
        }
        
        const loadingContainer = document.querySelector('.loading-container');
        if (loadingContainer) {
            loadingContainer.style.opacity = '0';
            loadingContainer.style.transform = 'scale(0.95)';
            setTimeout(() => {
                if (loadingContainer.parentNode) {
                    loadingContainer.parentNode.removeChild(loadingContainer);
                }
            }, 400);
        }
    }
}

// Global instance
window.legalLoader = new LegalLoadingAnimator();</new_str>
