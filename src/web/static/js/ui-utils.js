/**
 * Shared UI utilities for TutorialMaker web interface
 * Contains common button management and status functions
 */

// Button state management utilities
function setButtonDisabled(button, disabled, loadingText = null) {
    if (!button) return;
    
    button.disabled = disabled;
    
    if (loadingText && disabled) {
        button.setAttribute('data-original-text', button.textContent);
        button.textContent = loadingText;
    } else if (!disabled && button.hasAttribute('data-original-text')) {
        button.textContent = button.getAttribute('data-original-text');
        button.removeAttribute('data-original-text');
    }
}

function setButtonsDisabled(selectors, disabled) {
    selectors.forEach(selector => {
        const buttons = typeof selector === 'string' 
            ? document.querySelectorAll(selector)
            : [selector];
        
        buttons.forEach(button => {
            if (button) {
                button.disabled = disabled;
                button.style.opacity = disabled ? '0.6' : '1';
                
                if (button.tagName.toLowerCase() === 'a') {
                    button.style.pointerEvents = disabled ? 'none' : 'auto';
                }
            }
        });
    });
}

// Alert/notification system
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.temp-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} temp-alert`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        padding: 12px 16px;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease-out;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#d4edda',
        error: '#f8d7da',
        warning: '#fff3cd',
        info: '#d1ecf1'
    };
    const textColors = {
        success: '#155724',
        error: '#721c24',
        warning: '#856404',
        info: '#0c5460'
    };
    
    alertDiv.style.backgroundColor = colors[type] || colors.info;
    alertDiv.style.color = textColors[type] || textColors.info;
    alertDiv.style.border = `1px solid ${colors[type] || colors.info}`;
    
    alertDiv.textContent = message;
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '×';
    closeButton.style.cssText = `
        float: right;
        margin-left: 10px;
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        color: inherit;
        opacity: 0.7;
    `;
    closeButton.onclick = () => alertDiv.remove();
    
    alertDiv.appendChild(closeButton);
    document.body.appendChild(alertDiv);
    
    // Add slide-in animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    if (!document.querySelector('#alert-animations')) {
        style.id = 'alert-animations';
        document.head.appendChild(style);
    }
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            alertDiv.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => alertDiv.remove(), 300);
        }, duration);
    }
}

// Loading overlay utilities
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: #333;
        padding: 20px 30px;
        border-radius: 8px;
        text-align: center;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
        border: 3px solid #555;
        border-top: 3px solid #fff;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin: 0 auto 15px;
    `;
    
    // Add spinner animation
    if (!document.querySelector('#spinner-animation')) {
        const style = document.createElement('style');
        style.id = 'spinner-animation';
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    content.appendChild(spinner);
    content.appendChild(document.createTextNode(message));
    overlay.appendChild(content);
    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Form validation utilities
function validateRequiredFields(formSelector) {
    const form = typeof formSelector === 'string' 
        ? document.querySelector(formSelector)
        : formSelector;
    
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        const value = field.value.trim();
        if (!value) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Generic confirmation dialog
function confirmAction(message, onConfirm, onCancel = null) {
    if (confirm(message)) {
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
        return true;
    } else {
        if (typeof onCancel === 'function') {
            onCancel();
        }
        return false;
    }
}