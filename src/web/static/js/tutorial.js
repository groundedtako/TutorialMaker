// Tutorial page JavaScript
// This file is loaded after tutorialConfig is defined in the template

let hasChanges = false;
let originalData = {};
let loadingProgress = 0;
let totalSteps = 0;

// Loading overlay management
function updateLoadingProgress(progress, status) {
    const progressBar = document.getElementById('loading-progress');
    const statusText = document.getElementById('loading-status');
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    if (statusText) {
        statusText.textContent = status;
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
        }, 300);
    }
}

// Store original data and attach event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize loading progress
    updateLoadingProgress(10, 'Loading tutorial data...');
    
    // Store original data
    originalData.title = document.getElementById('tutorial-title').textContent;
    originalData.description = document.getElementById('tutorial-description').value;
    originalData.steps = {};

    updateLoadingProgress(30, 'Processing steps...');

    document.querySelectorAll('.step-description').forEach(desc => {
        const stepId = desc.closest('.tutorial-step').dataset.stepId;
        originalData.steps[stepId] = desc.textContent;
    });

    updateLoadingProgress(50, 'Initializing animations...');

    // Initialize animated click indicators
    initializeClickAnimations();

    updateLoadingProgress(70, 'Setting up event listeners...');

    // Attach change tracking event listeners - MUST be inside DOMContentLoaded
    document.getElementById('tutorial-title').addEventListener('input', markChanged);
    document.getElementById('tutorial-description').addEventListener('input', markChanged);

    document.querySelectorAll('.step-description').forEach(desc => {
        desc.addEventListener('input', function() {
            markChanged();
            this.classList.add('changed');
        });
    });

    updateLoadingProgress(90, 'Loading images...');

    // Wait for images to load, then hide overlay
    const images = document.querySelectorAll('.step-screenshot');
    totalSteps = images.length;
    
    if (totalSteps === 0) {
        // No images to load, hide overlay immediately
        updateLoadingProgress(100, 'Ready!');
        setTimeout(hideLoadingOverlay, 500);
    } else {
        let loadedImages = 0;
        
        images.forEach((img, index) => {
            if (img.complete) {
                loadedImages++;
            } else {
                img.addEventListener('load', function() {
                    loadedImages++;
                    const progress = 90 + (loadedImages / totalSteps) * 10;
                    updateLoadingProgress(progress, `Loading images... (${loadedImages}/${totalSteps})`);
                    
                    if (loadedImages === totalSteps) {
                        updateLoadingProgress(100, 'Ready!');
                        setTimeout(hideLoadingOverlay, 500);
                    }
                });
                
                img.addEventListener('error', function() {
                    loadedImages++;
                    const progress = 90 + (loadedImages / totalSteps) * 10;
                    updateLoadingProgress(progress, `Loading images... (${loadedImages}/${totalSteps})`);
                    
                    if (loadedImages === totalSteps) {
                        updateLoadingProgress(100, 'Ready!');
                        setTimeout(hideLoadingOverlay, 500);
                    }
                });
            }
        });
        
        // Check if all images are already loaded
        if (loadedImages === totalSteps) {
            updateLoadingProgress(100, 'Ready!');
            setTimeout(hideLoadingOverlay, 500);
        }
    }
});

// Initialize animated click indicators with intersection observer
function initializeClickAnimations() {
    // Handle legacy coordinates (convert absolute to percentage)
    document.querySelectorAll('.click-indicator.legacy-coords').forEach(indicator => {
        const img = indicator.closest('.screenshot-container').querySelector('.step-screenshot');
        const x = parseFloat(indicator.dataset.x);
        const y = parseFloat(indicator.dataset.y);

        img.onload = function() {
            const x_pct = (x / img.naturalWidth) * 100;
            const y_pct = (y / img.naturalHeight) * 100;
            indicator.style.left = `calc(${x_pct}% - 20px)`;
            indicator.style.top = `calc(${y_pct}% - 20px)`;
            indicator.classList.remove('legacy-coords');
        };

        // If image is already loaded
        if (img.complete && img.naturalWidth > 0) {
            img.onload();
        }
    });

    // Intersection Observer for click animations - triggers EVERY time step comes into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('step-visible');
                // Trigger animation with slight delay for better effect
                setTimeout(() => {
                    const clickCircles = entry.target.querySelectorAll('.click-circle');
                    clickCircles.forEach(circle => {
                        // Reset animation by removing and re-adding the class
                        circle.style.animation = 'none';
                        circle.offsetHeight; // Force reflow
                        circle.style.animation = 'clickContract 1.5s ease-out forwards';

                        // Add persistent state after animation completes
                        setTimeout(() => {
                            entry.target.classList.add('step-animation-complete');
                        }, 1500);
                    });
                }, 200);
            } else {
                // Keep the visible state even when out of view, only remove if user scrolls way past
                // This ensures circles remain visible once animated
                const rect = entry.target.getBoundingClientRect();
                if (rect.top > window.innerHeight + 200 || rect.bottom < -200) {
                    entry.target.classList.remove('step-visible', 'step-animation-complete');
                }
            }
        });
    }, {
        threshold: 0.3, // Trigger when 30% of step is visible
        rootMargin: '0px 0px -50px 0px' // Account for header/footer
    });

    // Observe all tutorial steps
    document.querySelectorAll('.tutorial-step').forEach(step => {
        observer.observe(step);
    });
}

function markChanged() {
    hasChanges = true;
    document.querySelector('[onclick="saveTutorial()"]').style.background = '#ffc107';
    document.querySelector('[onclick="saveTutorial()"]').textContent = 'Save Changes *';
}

function toggleScreenshotSize(img) {
    img.classList.toggle('fullsize');
}

async function deleteStep(stepId) {
    if (!confirm('Are you sure you want to delete this step?')) {
        return;
    }

    try {
        const response = await fetch(`/api/tutorial/${tutorialConfig.tutorialId}/delete_step`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                step_id: stepId
            })
        });

        const result = await response.json();

        if (result.success) {
            const stepElement = document.querySelector(`[data-step-id="${stepId}"]`);
            stepElement.classList.add('deleted');

            setTimeout(() => {
                stepElement.remove();
                updateStepNumbers();
                document.getElementById('step-count').textContent = result.new_step_count;
                showAlert('Step deleted successfully', 'success');
            }, 300);
        } else {
            showAlert('Failed to delete step: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showAlert('Delete failed: ' + error.message, 'error');
    }
}

function updateStepNumbers() {
    const steps = document.querySelectorAll('.tutorial-step:not(.deleted)');
    steps.forEach((step, index) => {
        const stepNumber = step.querySelector('.step-number');
        stepNumber.textContent = index + 1;
    });
}

// Utility function to disable/enable action buttons
function setActionButtonsDisabled(disabled) {
    const saveButton = document.querySelector('[onclick*="saveTutorial()"]');
    const exportButton = document.querySelector('[onclick*="exportTutorial()"]');
    const previewButton = document.querySelector('[onclick*="previewTutorial()"]');

    if (saveButton) {
        saveButton.disabled = disabled;
        saveButton.textContent = disabled ? 'Saving...' : 'Save Changes';
    }

    if (exportButton) {
        exportButton.disabled = disabled;
        exportButton.textContent = disabled ? 'Exporting...' : 'Export Selected Formats';
    }

    if (previewButton) {
        previewButton.disabled = disabled;
    }
}

// Helper function to convert HTML from contenteditable to plain text with newlines
function htmlToText(element) {
    // Clone the element to avoid modifying the original
    const clone = element.cloneNode(true);

    // Replace <br> tags with newlines
    clone.querySelectorAll('br').forEach(br => {
        br.replaceWith('\n');
    });

    // Replace </div> with newlines (contenteditable creates divs for new lines in some browsers)
    const html = clone.innerHTML;
    const textWithNewlines = html
        .replace(/<div>/gi, '\n')
        .replace(/<\/div>/gi, '')
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/&nbsp;/g, ' ')
        .replace(/<[^>]+>/g, ''); // Remove remaining HTML tags

    // Decode HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = textWithNewlines;
    return textarea.value;
}

async function saveTutorial() {
    // Disable buttons during save operation
    setActionButtonsDisabled(true);

    try {
        const title = document.getElementById('tutorial-title').textContent.trim();
        const description = document.getElementById('tutorial-description').value.trim();

        const steps = [];
        document.querySelectorAll('.tutorial-step:not(.deleted)').forEach(stepEl => {
            const stepId = stepEl.dataset.stepId;
            const descriptionEl = stepEl.querySelector('.step-description');

            // Convert HTML to text while preserving newlines
            const descriptionText = htmlToText(descriptionEl);

            steps.push({
                step_id: stepId,
                description: descriptionText.trim()
            });
        });

        const response = await fetch(`/api/tutorial/${tutorialConfig.tutorialId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                metadata: {
                    title: title,
                    description: description
                },
                steps: steps
            })
        });

        const result = await response.json();

        if (result.success) {
            hasChanges = false;
            document.querySelector('[onclick="saveTutorial()"]').style.background = '#28a745';
            document.querySelector('[onclick="saveTutorial()"]').textContent = 'Save Changes';

            // Remove change indicators
            document.querySelectorAll('.changed').forEach(el => {
                el.classList.remove('changed');
            });

            showAlert('Tutorial saved successfully!', 'success');
        } else {
            showAlert('Save failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showAlert('Save failed: ' + error.message, 'error');
    } finally {
        // Re-enable buttons after save completes or fails
        setActionButtonsDisabled(false);
    }
}

async function exportTutorial() {
    const formats = [];
    if (document.getElementById('export-html').checked) formats.push('html');
    if (document.getElementById('export-word').checked) formats.push('word');
    if (document.getElementById('export-markdown').checked) formats.push('markdown');

    if (formats.length === 0) {
        showAlert('Please select at least one export format', 'error');
        return;
    }

    // Disable buttons during export operation
    setActionButtonsDisabled(true);

    try {
        showAlert(`Exporting to ${formats.join(', ')}...`, 'info');

        const response = await fetch(`/api/tutorial/${tutorialConfig.tutorialId}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                formats: formats
            })
        });

        const result = await response.json();

        if (result.success) {
            showAlert('Tutorial exported successfully!', 'success');

            // Show results
            let message = 'Export completed:\n';
            for (const [format, path] of Object.entries(result.results)) {
                if (path.startsWith('Error:')) {
                    message += `\u2022 ${format.toUpperCase()}: ${path}\n`;
                } else {
                    const filename = path.split('/').pop();
                    message += `\u2022 ${format.toUpperCase()}: ${filename}\n`;
                }
            }

            showAlert(message, 'success');
        } else {
            showAlert('Export failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showAlert('Export failed: ' + error.message, 'error');
    } finally {
        // Re-enable buttons after export completes or fails
        setActionButtonsDisabled(false);
    }
}

function previewTutorial() {
    // Generate live preview of current tutorial
    const previewUrl = `/preview/${tutorialConfig.tutorialId}`;
    window.open(previewUrl, '_blank');
}

// Warn about unsaved changes
window.addEventListener('beforeunload', function(e) {
    if (hasChanges) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// Frontend logging for tutorial page
console.group('Tutorial Page Loaded');
console.log('Tutorial ID:', tutorialConfig.tutorialId);
console.log('Title:', tutorialConfig.title);
console.log('Steps count:', tutorialConfig.stepsCount);
console.log('Status:', tutorialConfig.status);
console.log('Created:', tutorialConfig.createdAt);
console.log('Page loaded at:', new Date().toISOString());
console.groupEnd();

// Log step data for debugging
if (tutorialConfig.steps && tutorialConfig.steps.length > 0) {
    console.group('Tutorial Steps Debug');
    tutorialConfig.steps.forEach((step, index) => {
        console.log(`Step ${step.step_number}:`, {
            id: step.step_id,
            description: step.description,
            screenshot: step.screenshot_path,
            coordinates: step.coordinates || null,
            ocr_confidence: step.ocr_confidence || 0,
            type: step.step_type
        });
    });
    console.groupEnd();
}

// Toggle export dropdown menu
function toggleExportDropdown() {
    const dropdown = document.getElementById('export-dropdown');
    dropdown.classList.toggle('show');
}

// Toggle formatting dropdown menu
function toggleFormattingDropdown() {
    const dropdown = document.getElementById('formatting-dropdown');
    dropdown.classList.toggle('show');
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const exportDropdown = document.getElementById('export-dropdown');
    const formattingDropdown = document.getElementById('formatting-dropdown');
    const dropdownContainer = event.target.closest('.dropdown-container');

    if (!dropdownContainer) {
        if (exportDropdown && exportDropdown.classList.contains('show')) {
            exportDropdown.classList.remove('show');
        }
        if (formattingDropdown && formattingDropdown.classList.contains('show')) {
            formattingDropdown.classList.remove('show');
        }
    }
});
