/**
 * API utilities for TutorialMaker web interface
 * Contains common API call patterns and response handling
 */

// Common API request wrapper
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };
    
    try {
        const response = await fetch(url, defaultOptions);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return result;
    } catch (error) {
        console.error(`API request failed: ${url}`, error);
        throw error;
    }
}

// Tutorial management API calls
const TutorialAPI = {
    // Export tutorial to specified formats
    async exportTutorial(tutorialId, formats) {
        return await apiRequest(`/api/tutorial/${tutorialId}/export`, {
            method: 'POST',
            body: JSON.stringify({ formats })
        });
    },
    
    // Update tutorial metadata and steps
    async updateTutorial(tutorialId, data) {
        return await apiRequest(`/api/tutorial/${tutorialId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    // Delete tutorial
    async deleteTutorial(tutorialId) {
        return await apiRequest(`/api/tutorial/${tutorialId}`, {
            method: 'DELETE'
        });
    },
    
    // Delete specific step
    async deleteStep(tutorialId, stepId) {
        return await apiRequest(`/api/tutorial/${tutorialId}/step/${stepId}`, {
            method: 'DELETE'
        });
    },
    
    // Get tutorial file information
    async getFileInfo(tutorialId) {
        return await apiRequest(`/api/tutorial/${tutorialId}/files`);
    },
    
    // Open file location
    async openFileLocation(tutorialId, fileType) {
        return await apiRequest(`/api/tutorial/${tutorialId}/open_location`, {
            method: 'POST',
            body: JSON.stringify({ file_type: fileType })
        });
    },
    
    // Export all tutorials
    async exportAllTutorials(formats) {
        return await apiRequest('/api/export_all', {
            method: 'POST',
            body: JSON.stringify({ formats })
        });
    }
};

// Recording API calls
const RecordingAPI = {
    // Start new recording session
    async startRecording(tutorialName) {
        return await apiRequest('/api/recording/start', {
            method: 'POST',
            body: JSON.stringify({ tutorial_name: tutorialName })
        });
    },
    
    // Stop recording session  
    async stopRecording() {
        return await apiRequest('/api/recording/stop', {
            method: 'POST'
        });
    },
    
    // Pause recording session
    async pauseRecording() {
        return await apiRequest('/api/recording/pause', {
            method: 'POST'
        });
    },
    
    // Resume recording session
    async resumeRecording() {
        return await apiRequest('/api/recording/resume', {
            method: 'POST'
        });
    },
    
    // Get recording status
    async getStatus() {
        return await apiRequest('/api/recording/status');
    }
};

// Response handling utilities
function handleApiResponse(response, successMessage = null, errorPrefix = 'Operation failed') {
    if (response.success) {
        if (successMessage) {
            showAlert(successMessage, 'success');
        }
        return response.data || response;
    } else {
        const errorMessage = response.error || 'Unknown error occurred';
        showAlert(`${errorPrefix}: ${errorMessage}`, 'error');
        throw new Error(errorMessage);
    }
}

// Batch operations with progress
async function batchOperation(items, operation, progressCallback = null) {
    const results = [];
    let successCount = 0;
    let failedCount = 0;
    
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        
        try {
            const result = await operation(item, i);
            results.push({ success: true, item, result });
            successCount++;
        } catch (error) {
            results.push({ success: false, item, error: error.message });
            failedCount++;
            console.error(`Batch operation failed for item:`, item, error);
        }
        
        // Call progress callback if provided
        if (typeof progressCallback === 'function') {
            progressCallback({
                completed: i + 1,
                total: items.length,
                successCount,
                failedCount,
                currentItem: item
            });
        }
        
        // Small delay to prevent overwhelming the server
        if (i < items.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    return {
        results,
        summary: {
            total: items.length,
            successful: successCount,
            failed: failedCount,
            successRate: ((successCount / items.length) * 100).toFixed(1)
        }
    };
}

// File download utilities
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    downloadFile(url, filename);
    window.URL.revokeObjectURL(url);
}

// URL utilities
function getCurrentTutorialId() {
    const path = window.location.pathname;
    const match = path.match(/\/tutorial\/([^\/]+)/);
    return match ? match[1] : null;
}

function buildApiUrl(endpoint, params = {}) {
    const url = new URL(endpoint, window.location.origin);
    
    Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
            url.searchParams.append(key, params[key]);
        }
    });
    
    return url.toString();
}