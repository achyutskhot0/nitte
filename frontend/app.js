const API = window.location.origin;
let currentFileId = null;
let processingFiles = new Set();
let websocket = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadRecentFiles();
    setupEventListeners();
    connectWebSocket();
});

function setupEventListeners() {
    const fileInput = document.getElementById('file');
    fileInput?.addEventListener('change', handleFileSelection);
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = function(event) {
        console.log('WebSocket connected');
    };
    
    websocket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.log('WebSocket message:', event.data);
        }
    };
    
    websocket.onclose = function(event) {
        console.log('WebSocket disconnected, attempting to reconnect...');
        setTimeout(connectWebSocket, 3000);
    };
    
    websocket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

function handleWebSocketMessage(data) {
    if (data.type === 'progress') {
        updateProgress(data.progress, data.message);
        
        if (data.step === 'complete') {
            // Processing complete, hide progress after a delay
            setTimeout(() => {
                const progressContainer = document.getElementById('progress-container');
                if (progressContainer) {
                    progressContainer.style.display = 'none';
                }
            }, 2000);
        }
    }
}

function handleFileSelection() {
    const fileInput = document.getElementById('file');
    const files = Array.from(fileInput.files || []);
    const fileInfo = document.getElementById('file-info');
    const fileList = document.getElementById('file-list');
    
    if (files.length === 0) {
        fileInfo.style.display = 'none';
        document.getElementById('file-name').textContent = 'No files selected';
        return;
    }
    
    fileInfo.style.display = 'block';
    fileList.innerHTML = '';
    
    files.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div>
                <i class="fas fa-file-alt mr-2"></i>
                <span>${file.name}</span>
                <small class="has-text-grey ml-2">(${formatFileSize(file.size)})</small>
            </div>
            <button class="button is-small is-danger is-outlined" onclick="removeFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        fileList.appendChild(fileItem);
    });
    
    document.getElementById('file-name').textContent = `${files.length} file(s) selected`;
}

function removeFile(index) {
    const fileInput = document.getElementById('file');
    const dt = new DataTransfer();
    const files = Array.from(fileInput.files);
    
    files.forEach((file, i) => {
        if (i !== index) {
            dt.items.add(file);
        }
    });
    
    fileInput.files = dt.files;
    handleFileSelection();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function upload() {
  const files = document.getElementById('file').files;
    if (!files || files.length === 0) {
        showMessage('Please select at least one file', 'error');
        return;
    }
    
    const uploadBtn = document.getElementById('upload-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    // Show progress
    uploadBtn.disabled = true;
    progressContainer.style.display = 'block';
    updateProgress(0, 'Uploading files...');
    
    try {
  const fd = new FormData();
        for (const f of files) {
            fd.append('files', f);
            processingFiles.add(f.name);
        }
        
        const response = await fetch(API + "/upload", { 
            method: "POST", 
            body: fd 
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        updateProgress(25, 'Files uploaded successfully');
        
        // Process each file
        for (let i = 0; i < result.file_ids.length; i++) {
            const fileId = result.file_ids[i];
            const fileName = Array.from(files)[i].name;
            
            updateProgress(25 + (i * 25), `Processing ${fileName}...`);
            await loadSummary(fileId);
        }
        
        updateProgress(100, 'Processing complete!');
        showMessage('Documents processed successfully!', 'success');
        
        // Clear file input and update recent files
        document.getElementById('file').value = '';
        handleFileSelection();
        loadRecentFiles();
        
    } catch (error) {
        console.error('Upload error:', error);
        showMessage(`Upload failed: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 2000);
        processingFiles.clear();
    }
}

function updateProgress(percent, text) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    progressBar.value = percent;
    progressText.textContent = text;
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('status-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    messageDiv.innerHTML = `
        <div class="is-flex is-justify-content-space-between is-align-items-center">
            <span>${message}</span>
            <button class="delete" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    container.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 5000);
}

function switchTab(t, ev) {
    document.querySelectorAll('#tabs li').forEach(li => li.classList.remove('is-active'));
  ev?.target?.parentElement?.classList?.add('is-active');
  loadTab(t);
}

async function loadSummary(fid) {
    try {
        currentFileId = fid;
  const res = await fetch(API + "/summaries/" + fid, { method: 'POST' });
        
        if (!res.ok) {
            throw new Error(`Analysis failed: ${res.statusText}`);
        }
        
  const data = await res.json();
  window.data = data;
  switchTab('lawyer');
        
        // Store in recent files
        storeRecentFile(fid, data);
        
    } catch (error) {
        console.error('Summary loading error:', error);
        showMessage(`Analysis failed: ${error.message}`, 'error');
    }
}

function loadTab(t) {
  const box = document.getElementById('content');
    if (!window.data) {
        box.innerHTML = `
            <div class="has-text-centered has-text-grey">
                <i class="fas fa-file-alt fa-3x mb-4"></i>
                <p>Upload a document to see analysis results</p>
            </div>
        `;
        return;
    }
    
    let content = '';
    
    switch(t) {
        case 'lawyer':
            content = formatLawyerAnalysis(window.data.lawyer);
            break;
        case 'citizen':
            content = formatCitizenSummary(window.data.citizen);
            break;
        case 'next':
            content = formatNextSteps(window.data.next);
            break;
        case 'facts':
            content = formatKeyFacts(window.data.facts);
            break;
        default:
            content = '<p>Unknown tab</p>';
    }
    
    box.innerHTML = content;
}

function formatLawyerAnalysis(data) {
    if (data.error) {
        return `<div class="error-message">Error: ${data.error}</div>`;
    }
    
    const sections = [
        { key: 'issues', title: 'Legal Issues', icon: 'fas fa-exclamation-triangle' },
        { key: 'arguments', title: 'Key Arguments', icon: 'fas fa-gavel' },
        { key: 'precedents', title: 'Legal Precedents', icon: 'fas fa-book' },
        { key: 'outcome', title: 'Expected Outcome', icon: 'fas fa-flag-checkered' },
        { key: 'risks', title: 'Risks & Concerns', icon: 'fas fa-shield-alt' },
        { key: 'citations', title: 'Citations', icon: 'fas fa-quote-right' }
    ];
    
    return sections.map(section => {
        const value = data[section.key];
        if (!value || (Array.isArray(value) && value.length === 0)) {
            return '';
        }
        
        return `
            <div class="summary-section">
                <h3><i class="${section.icon} mr-2"></i>${section.title}</h3>
                <div class="content">
                    ${Array.isArray(value) ? 
                        `<ul>${value.map(item => `<li>${item}</li>`).join('')}</ul>` :
                        `<p>${value}</p>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

function formatCitizenSummary(data) {
    if (data.error) {
        return `<div class="error-message">Error: ${data.error}</div>`;
    }
    
    const sections = [
        { key: 'summary', title: 'Summary', icon: 'fas fa-clipboard-list' },
        { key: 'key_points', title: 'Key Points', icon: 'fas fa-key' },
        { key: 'what_it_means', title: 'What This Means', icon: 'fas fa-lightbulb' },
        { key: 'actions', title: 'Recommended Actions', icon: 'fas fa-tasks' },
        { key: 'risks', title: 'Important Risks', icon: 'fas fa-exclamation-circle' }
    ];
    
    return sections.map(section => {
        const value = data[section.key];
        if (!value || (Array.isArray(value) && value.length === 0)) {
            return '';
        }
        
        return `
            <div class="summary-section">
                <h3><i class="${section.icon} mr-2"></i>${section.title}</h3>
                <div class="content">
                    ${Array.isArray(value) ? 
                        `<ul>${value.map(item => `<li>${item}</li>`).join('')}</ul>` :
                        `<p>${value}</p>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

function formatNextSteps(data) {
    if (data.error) {
        return `<div class="error-message">Error: ${data.error}</div>`;
    }
    
    let content = '';
    
    if (data.deadlines && data.deadlines.length > 0) {
        content += `
            <div class="summary-section">
                <h3><i class="fas fa-calendar-alt mr-2"></i>Important Deadlines</h3>
                <div class="content">
                    <ul>
                        ${data.deadlines.map(deadline => `<li><strong>${deadline}</strong></li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    if (data.entities && data.entities.length > 0) {
        content += `
            <div class="summary-section">
                <h3><i class="fas fa-users mr-2"></i>Key Entities</h3>
                <div class="content">
                    <div class="tags">
                        ${data.entities.map(([entity, label]) => 
                            `<span class="tag is-info">${entity} <small>(${label})</small></span>`
                        ).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    return content || '<p>No specific next steps identified.</p>';
}

function formatKeyFacts(data) {
    if (data.error) {
        return `<div class="error-message">Error: ${data.error}</div>`;
    }
    
    if (!data || Object.keys(data).length === 0) {
        return '<p>No key facts extracted.</p>';
    }
    
    return Object.entries(data).map(([key, value]) => {
        if (!value || (Array.isArray(value) && value.length === 0)) {
            return '';
        }
        
        return `
            <div class="summary-section">
                <h3><i class="fas fa-info-circle mr-2"></i>${key.replace(/_/g, ' ').toUpperCase()}</h3>
                <div class="content">
                    ${Array.isArray(value) ? 
                        `<ul>${value.map(item => `<li>${item}</li>`).join('')}</ul>` :
                        `<p>${value}</p>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

// File management functions
function storeRecentFile(fileId, data) {
    const recentFiles = JSON.parse(localStorage.getItem('recentFiles') || '[]');
    const fileInfo = {
        id: fileId,
        timestamp: Date.now(),
        summary: data.lawyer?.summary || 'Legal document analysis'
    };
    
    // Remove if already exists
    const existingIndex = recentFiles.findIndex(f => f.id === fileId);
    if (existingIndex !== -1) {
        recentFiles.splice(existingIndex, 1);
    }
    
    // Add to beginning
    recentFiles.unshift(fileInfo);
    
    // Keep only last 10
    if (recentFiles.length > 10) {
        recentFiles.splice(10);
    }
    
    localStorage.setItem('recentFiles', JSON.stringify(recentFiles));
}

function loadRecentFiles() {
    const recentFiles = JSON.parse(localStorage.getItem('recentFiles') || '[]');
    const container = document.getElementById('recent-files');
    
    if (recentFiles.length === 0) {
        container.innerHTML = '<p class="has-text-grey">No recent files</p>';
        return;
    }
    
    container.innerHTML = recentFiles.map(file => `
        <div class="file-item">
            <div>
                <i class="fas fa-file-alt mr-2"></i>
                <span>${file.summary}</span>
                <br>
                <small class="has-text-grey">${new Date(file.timestamp).toLocaleDateString()}</small>
            </div>
            <button class="button is-small is-primary is-outlined" onclick="loadFile('${file.id}')">
                <i class="fas fa-eye"></i>
            </button>
        </div>
    `).join('');
}

async function loadFile(fileId) {
    try {
        await loadSummary(fileId);
        showMessage('File loaded successfully', 'success');
    } catch (error) {
        showMessage(`Failed to load file: ${error.message}`, 'error');
    }
}

function showFileManager() {
    const modal = document.getElementById('file-manager-modal');
    const content = document.getElementById('file-manager-content');
    
    // Load files from backend
    fetch(API + '/files')
        .then(response => response.json())
        .then(files => {
            if (files.length === 0) {
                content.innerHTML = '<p>No files found</p>';
            } else {
                content.innerHTML = files.map(file => `
                    <div class="file-item">
                        <div>
                            <i class="fas fa-file-alt mr-2"></i>
                            <span>${file.name}</span>
                            <br>
                            <small class="has-text-grey">${new Date(file.uploaded_at).toLocaleDateString()}</small>
                        </div>
                        <div class="buttons">
                            <button class="button is-small is-primary is-outlined" onclick="loadFile('${file.id}')">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="button is-small is-danger is-outlined" onclick="deleteFile('${file.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        })
        .catch(error => {
            content.innerHTML = `<p class="has-text-danger">Error loading files: ${error.message}</p>`;
        });
    
    modal.classList.add('is-active');
}

function hideFileManager() {
    const modal = document.getElementById('file-manager-modal');
    modal.classList.remove('is-active');
}

async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }
    
    try {
        const response = await fetch(API + `/files/${fileId}`, { method: 'DELETE' });
        if (response.ok) {
            showMessage('File deleted successfully', 'success');
            showFileManager(); // Refresh the list
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        showMessage(`Failed to delete file: ${error.message}`, 'error');
    }
}

function exportResults() {
    if (!window.data) {
        showMessage('No data to export', 'error');
        return;
    }
    
    const exportData = {
        timestamp: new Date().toISOString(),
        fileId: currentFileId,
        ...window.data
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `legal-analysis-${currentFileId || 'unknown'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showMessage('Results exported successfully', 'success');
}

// Make functions globally available
window.upload = upload;
window.switchTab = switchTab;
window.removeFile = removeFile;
window.showFileManager = showFileManager;
window.hideFileManager = hideFileManager;
window.deleteFile = deleteFile;
window.exportResults = exportResults;
window.loadFile = loadFile;
