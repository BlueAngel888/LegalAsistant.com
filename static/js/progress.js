/**
 * Progress indicator system for file processing
 */

class ProgressIndicator {
    constructor() {
        this.progressOverlay = null;
        this.progressCircle = null;
        this.progressText = null;
        this.currentProgress = 0;
        this.isVisible = false;
    }

    createProgressOverlay() {
        if (this.progressOverlay) return;

        // Create overlay
        this.progressOverlay = document.createElement('div');
        this.progressOverlay.className = 'progress-overlay';
        this.progressOverlay.innerHTML = `
            <div class="progress-container">
                <div class="progress-circle">
                    <svg width="120" height="120" viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="50" stroke="#e0e0e0" stroke-width="8" fill="none"/>
                        <circle cx="60" cy="60" r="50" stroke="#007bff" stroke-width="8" fill="none"
                                stroke-dasharray="314.16" stroke-dashoffset="314.16" 
                                class="progress-circle-bar" transform="rotate(-90 60 60)"/>
                    </svg>
                    <div class="progress-percentage">0%</div>
                </div>
                <div class="progress-message">Se procesează documentele...</div>
                <div class="progress-details">Vă rugăm să așteptați</div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .progress-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                backdrop-filter: blur(5px);
            }

            .progress-container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 350px;
                width: 90%;
            }

            .progress-circle {
                position: relative;
                display: inline-block;
                margin-bottom: 20px;
            }

            .progress-circle svg {
                transform: rotate(-90deg);
            }

            .progress-circle-bar {
                transition: stroke-dashoffset 0.5s ease-in-out;
            }

            .progress-percentage {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
            }

            .progress-message {
                font-size: 18px;
                font-weight: 600;
                color: #333;
                margin-bottom: 10px;
            }

            .progress-details {
                font-size: 14px;
                color: #666;
                margin-bottom: 20px;
            }

            .progress-steps {
                text-align: left;
                margin-top: 20px;
            }

            .progress-step {
                display: flex;
                align-items: center;
                margin-bottom: 8px;
                font-size: 14px;
            }

            .progress-step-icon {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
            }

            .progress-step.completed .progress-step-icon {
                background: #28a745;
                color: white;
            }

            .progress-step.active .progress-step-icon {
                background: #007bff;
                color: white;
                animation: pulse 1.5s infinite;
            }

            .progress-step.pending .progress-step-icon {
                background: #e0e0e0;
                color: #666;
            }

            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(this.progressOverlay);

        this.progressCircle = this.progressOverlay.querySelector('.progress-circle-bar');
        this.progressText = this.progressOverlay.querySelector('.progress-percentage');
    }

    show(message = 'Se procesează documentele...') {
        this.createProgressOverlay();
        this.progressOverlay.querySelector('.progress-message').textContent = message;
        this.progressOverlay.style.display = 'flex';
        this.isVisible = true;
        this.updateProgress(0);
    }

    hide() {
        if (this.progressOverlay) {
            this.progressOverlay.style.display = 'none';
            this.isVisible = false;
        }
    }

    updateProgress(percentage, details = '') {
        this.currentProgress = Math.min(100, Math.max(0, percentage));
        
        if (this.progressText) {
            this.progressText.textContent = `${Math.round(this.currentProgress)}%`;
        }

        if (this.progressCircle) {
            const circumference = 314.16; // 2 * π * 50
            const offset = circumference - (this.currentProgress / 100) * circumference;
            this.progressCircle.style.strokeDashoffset = offset;
        }

        if (details && this.progressOverlay) {
            this.progressOverlay.querySelector('.progress-details').textContent = details;
        }
    }

    addSteps(steps) {
        if (!this.progressOverlay) return;
        
        const container = this.progressOverlay.querySelector('.progress-container');
        let stepsContainer = container.querySelector('.progress-steps');
        
        if (!stepsContainer) {
            stepsContainer = document.createElement('div');
            stepsContainer.className = 'progress-steps';
            container.appendChild(stepsContainer);
        }

        stepsContainer.innerHTML = '';
        steps.forEach((step, index) => {
            const stepEl = document.createElement('div');
            stepEl.className = 'progress-step pending';
            stepEl.innerHTML = `
                <div class="progress-step-icon">${index + 1}</div>
                <div class="progress-step-text">${step}</div>
            `;
            stepsContainer.appendChild(stepEl);
        });
    }

    updateStep(stepIndex, status = 'active') {
        const steps = this.progressOverlay?.querySelectorAll('.progress-step');
        if (steps && steps[stepIndex]) {
            steps[stepIndex].className = `progress-step ${status}`;
            if (status === 'completed') {
                steps[stepIndex].querySelector('.progress-step-icon').innerHTML = '✓';
            }
        }
    }
}

// Global progress indicator instance
window.progressIndicator = new ProgressIndicator();

// Auto-show progress on form submission for file uploads
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const files = document.getElementById('files').files;
            const cameraFiles = document.querySelector('input[name="camera"]')?.files;
            const totalFiles = (files?.length || 0) + (cameraFiles?.length || 0);
            
            if (totalFiles > 0) {
                window.progressIndicator.show('Se procesează documentele...');
                
                const steps = [
                    'Validarea fișierelor',
                    'Extragerea textului',
                    'Verificarea consistenței',
                    'Pregătirea pentru plată'
                ];
                
                window.progressIndicator.addSteps(steps);
                
                // Simulate progress
                let currentStep = 0;
                let progress = 0;
                
                const updateProgress = () => {
                    if (currentStep < steps.length) {
                        window.progressIndicator.updateStep(currentStep, 'active');
                        progress += 25;
                        window.progressIndicator.updateProgress(progress, steps[currentStep]);
                        
                        setTimeout(() => {
                            window.progressIndicator.updateStep(currentStep, 'completed');
                            currentStep++;
                            if (currentStep < steps.length) {
                                setTimeout(updateProgress, 500);
                            }
                        }, totalFiles > 3 ? 1000 : 2000);
                    }
                };
                
                setTimeout(updateProgress, 500);
            }
        });
    }
});