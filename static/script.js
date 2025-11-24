// API Base URL
const API_BASE = '';

// State
let allColors = [];
let currentVideos = [];
let scrapingInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadTags();
    loadVideos();
    checkScrapingStatus(); // Check if scraping is already running
    
    // Enter key support for search
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchVideos();
    });
    
    document.getElementById('lyricInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchByLyric();
    });
});

// Load database statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();
        
        const statsHTML = `
            <span class="stat-item">📹 ${data.total_videos || 0} Videos</span>
            <span class="stat-item">🏷️ ${data.unique_tags || 0} Tags</span>
            <span class="stat-item">🎨 ${data.unique_colors || 0} Colors</span>
        `;
        
        document.getElementById('stats').innerHTML = statsHTML;
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('stats').innerHTML = '<span class="stat-item">⚠️ Error loading stats</span>';
    }
}

// Load tags for filters
async function loadTags() {
    try {
        const response = await fetch(`${API_BASE}/api/tags`);
        const data = await response.json();
        
        // Populate color filter
        const colorFilter = document.getElementById('colorFilter');
        if (data.colors && data.colors.length > 0) {
            data.colors.forEach(color => {
                const option = document.createElement('option');
                option.value = color;
                option.textContent = color.charAt(0).toUpperCase() + color.slice(1);
                colorFilter.appendChild(option);
            });
        }
        
        allColors = data.colors || [];
    } catch (error) {
        console.error('Error loading tags:', error);
    }
}

// Load videos with filters
async function loadVideos() {
    showLoading();
    
    try {
        const keywords = document.getElementById('searchInput').value.trim();
        const mood = document.getElementById('moodFilter').value;
        const color = document.getElementById('colorFilter').value;
        const limit = document.getElementById('limitFilter').value;
        
        const params = new URLSearchParams();
        if (keywords) params.append('keywords', keywords);
        if (mood) params.append('mood', mood);
        if (color) params.append('color', color);
        if (limit) params.append('limit', limit);
        
        const response = await fetch(`${API_BASE}/api/videos?${params}`);
        const data = await response.json();
        
        currentVideos = data.videos || [];
        displayVideos(currentVideos);
    } catch (error) {
        console.error('Error loading videos:', error);
        hideLoading();
        showError('Failed to load videos. Please try again.');
    }
}

// Display videos in grid
function displayVideos(videos) {
    hideLoading();
    
    const videoGrid = document.getElementById('videoGrid');
    const resultsInfo = document.getElementById('resultsInfo');
    const resultsCount = document.getElementById('resultsCount');
    const noResults = document.getElementById('noResults');
    
    if (!videos || videos.length === 0) {
        videoGrid.innerHTML = '';
        resultsInfo.style.display = 'none';
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    resultsInfo.style.display = 'block';
    resultsCount.textContent = `${videos.length} video${videos.length !== 1 ? 's' : ''} found`;
    
    videoGrid.innerHTML = videos.map(video => createVideoCard(video)).join('');
}

// Create video card HTML
function createVideoCard(video) {
    const mood = video.moods && video.moods.length > 0 ? video.moods[0].mood_type : 'neutral';
    const moodClass = `mood-${mood}`;
    
    const tags = video.tags || [];
    const themeTags = tags.filter(t => t.tag_type === 'theme' || t.tag_type === 'keyword').slice(0, 3);
    
    const thumbnail = video.thumbnail || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="280" height="180"%3E%3Crect fill="%23667eea" width="280" height="180"/%3E%3Ctext fill="white" font-family="Arial" font-size="20" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Preview%3C/text%3E%3C/svg%3E';
    
    const fileName = video.file_path ? video.file_path.split(/[/\\]/).pop() : 'Unknown';
    const duration = video.duration ? `${video.duration.toFixed(1)}s` : '';
    
    return `
        <div class="video-card" onclick="showVideoDetails(${video.id})">
            <img src="${thumbnail}" alt="${fileName}" class="video-thumbnail" loading="lazy">
            <div class="video-info">
                <div class="video-title" title="${fileName}">${fileName}</div>
                <div class="video-meta">
                    ${duration ? `<span class="meta-tag">${duration}</span>` : ''}
                    <span class="meta-tag ${moodClass}">${mood}</span>
                </div>
                <div class="video-tags">
                    ${themeTags.map(tag => `<span class="tag">${tag.tag_value}</span>`).join('')}
                </div>
            </div>
        </div>
    `;
}

// Show video details in modal
async function showVideoDetails(videoId) {
    try {
        const response = await fetch(`${API_BASE}/api/video/${videoId}/details`);
        const video = await response.json();
        
        const modal = document.getElementById('videoModal');
        const modalBody = document.getElementById('modalBody');
        
        const colors = video.colors || [];
        const tags = video.tags || [];
        const moods = video.moods || [];
        
        const colorPalette = colors.length > 0 
            ? colors.map(c => `
                <div class="color-swatch" 
                     style="background-color: ${c.color_hex}" 
                     data-name="${c.color_name || c.color_hex}"
                     title="${c.color_name || c.color_hex} (${(c.percentage * 100).toFixed(1)}%)">
                </div>
            `).join('')
            : '<p>No color data</p>';
        
        const tagsByType = {};
        tags.forEach(tag => {
            if (!tagsByType[tag.tag_type]) {
                tagsByType[tag.tag_type] = [];
            }
            tagsByType[tag.tag_type].push(tag.tag_value);
        });
        
        const fileName = video.file_path ? video.file_path.split(/[/\\]/).pop() : 'Unknown';
        
        modalBody.innerHTML = `
            <video class="modal-video" controls autoplay>
                <source src="${API_BASE}/api/video/${videoId}" type="video/mp4">
                Your browser does not support video playback.
            </video>
            
            <div class="modal-details">
                <h2>${fileName}</h2>
                
                <div class="detail-section">
                    <h3>📊 Video Info</h3>
                    <div class="tags-list">
                        ${video.duration ? `<span class="detail-tag">Duration: ${video.duration.toFixed(2)}s</span>` : ''}
                        ${video.width && video.height ? `<span class="detail-tag">Resolution: ${video.width}x${video.height}</span>` : ''}
                        ${video.file_size ? `<span class="detail-tag">Size: ${(video.file_size / 1024 / 1024).toFixed(2)} MB</span>` : ''}
                    </div>
                </div>
                
                ${moods.length > 0 ? `
                <div class="detail-section">
                    <h3>😊 Mood</h3>
                    <div class="tags-list">
                        ${moods.map(m => `
                            <span class="detail-tag mood-${m.mood_type}">
                                ${m.mood_type} ${m.intensity ? `(${m.intensity}/10)` : ''}
                            </span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${colors.length > 0 ? `
                <div class="detail-section">
                    <h3>🎨 Color Palette</h3>
                    <div class="color-palette">
                        ${colorPalette}
                    </div>
                </div>
                ` : ''}
                
                ${Object.keys(tagsByType).length > 0 ? `
                <div class="detail-section">
                    <h3>🏷️ Tags</h3>
                    ${Object.entries(tagsByType).map(([type, values]) => `
                        <p><strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong></p>
                        <div class="tags-list">
                            ${values.map(v => `<span class="detail-tag">${v}</span>`).join('')}
                        </div>
                    `).join('')}
                </div>
                ` : ''}
                
                ${video.source_url ? `
                <div class="detail-section">
                    <h3>🔗 Source</h3>
                    <a href="${video.source_url}" target="_blank" rel="noopener">${video.source_url}</a>
                </div>
                ` : ''}
            </div>
        `;
        
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error loading video details:', error);
        alert('Failed to load video details.');
    }
}

// Close modal
function closeModal() {
    const modal = document.getElementById('videoModal');
    const video = modal.querySelector('video');
    if (video) {
        video.pause();
    }
    modal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('videoModal');
    if (event.target === modal) {
        closeModal();
    }
};

// Search by lyric
async function searchByLyric() {
    const lyric = document.getElementById('lyricInput').value.trim();
    const mood = document.getElementById('lyricMood').value;
    
    if (!lyric) {
        alert('Please enter a lyric line');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/search/lyric`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ lyric, mood: mood || null })
        });
        
        const data = await response.json();
        
        if (data.video) {
            displayVideos([data.video]);
        } else {
            hideLoading();
            alert('No matching video found for this lyric.');
        }
    } catch (error) {
        console.error('Error searching by lyric:', error);
        hideLoading();
        alert('Failed to search. Please try again.');
    }
}

// Search videos (button click or Enter key)
function searchVideos() {
    loadVideos();
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('moodFilter').value = '';
    document.getElementById('colorFilter').value = '';
    document.getElementById('limitFilter').value = '50';
    document.getElementById('lyricInput').value = '';
    document.getElementById('lyricMood').value = '';
    loadVideos();
}

// Show loading state
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('videoGrid').style.display = 'none';
    document.getElementById('resultsInfo').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
}

// Hide loading state
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('videoGrid').style.display = 'grid';
}

// Show error message
function showError(message) {
    const videoGrid = document.getElementById('videoGrid');
    videoGrid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 40px; background: white; border-radius: 15px;">
            <p style="color: #d9534f; font-size: 1.2rem;">⚠️ ${message}</p>
        </div>
    `;
    videoGrid.style.display = 'grid';
}

// Scraping Control Functions

async function startScraping() {
    const queriesInput = document.getElementById('scrapingQueries').value.trim();
    const videosPerQuery = parseInt(document.getElementById('videosPerQuery').value);
    
    if (!queriesInput) {
        alert('Please enter search queries');
        return;
    }
    
    const queries = queriesInput.split(',').map(q => q.trim()).filter(q => q);
    
    if (queries.length === 0) {
        alert('Please enter at least one search query');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/scraping/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                queries: queries,
                videos_per_query: videosPerQuery
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show progress section
            document.getElementById('scrapingProgress').style.display = 'block';
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'inline-block';
            
            // Start polling for status
            startStatusPolling();
        } else {
            alert(`Error: ${data.error || 'Failed to start scraping'}`);
        }
    } catch (error) {
        console.error('Error starting scraping:', error);
        alert('Failed to start scraping. Please try again.');
    }
}

async function stopScraping() {
    try {
        const response = await fetch(`${API_BASE}/api/scraping/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            stopStatusPolling();
            document.getElementById('startBtn').style.display = 'inline-block';
            document.getElementById('stopBtn').style.display = 'none';
        } else {
            alert(`Error: ${data.error || 'Failed to stop scraping'}`);
        }
    } catch (error) {
        console.error('Error stopping scraping:', error);
        alert('Failed to stop scraping.');
    }
}

async function checkScrapingStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/scraping/status`);
        const state = await response.json();
        
        if (state.running) {
            // Scraping is already running, show progress
            document.getElementById('scrapingProgress').style.display = 'block';
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'inline-block';
            startStatusPolling();
        }
        
        updateProgressUI(state);
    } catch (error) {
        console.error('Error checking scraping status:', error);
    }
}

async function updateScrapingStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/scraping/status`);
        const state = await response.json();
        
        updateProgressUI(state);
        
        // If completed or error, stop polling and refresh videos
        if (!state.running && (state.status === 'completed' || state.status === 'error' || state.status === 'stopped')) {
            stopStatusPolling();
            
            if (state.status === 'completed') {
                // Reload videos and stats
                setTimeout(() => {
                    loadStats();
                    loadVideos();
                }, 1000);
            }
            
            // Reset UI after a delay
            setTimeout(() => {
                document.getElementById('startBtn').style.display = 'inline-block';
                document.getElementById('stopBtn').style.display = 'none';
                
                if (state.status === 'completed') {
                    document.getElementById('scrapingProgress').style.display = 'none';
                }
            }, 3000);
        }
    } catch (error) {
        console.error('Error updating scraping status:', error);
    }
}

function updateProgressUI(state) {
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');
    const progressPercent = document.getElementById('progressPercent');
    const progressTask = document.getElementById('progressTask');
    
    progressBar.style.width = `${state.progress || 0}%`;
    progressPercent.textContent = `${state.progress || 0}%`;
    
    let statusText = state.status.charAt(0).toUpperCase() + state.status.slice(1);
    if (state.error) {
        statusText = `Error: ${state.error}`;
        progressStatus.style.color = '#ff6b6b';
    } else if (state.status === 'completed') {
        statusText = '✅ Completed!';
        progressStatus.style.color = '#8bc34a';
    } else {
        progressStatus.style.color = '#ffa500';
    }
    
    progressStatus.textContent = statusText;
    progressTask.textContent = state.current_task || 'Processing...';
    
    // Update stats if available
    if (state.videos_processed || state.clips_created) {
        progressTask.textContent += ` (${state.videos_processed || 0} videos, ${state.clips_created || 0} clips)`;
    }
}

function startStatusPolling() {
    if (scrapingInterval) {
        clearInterval(scrapingInterval);
    }
    scrapingInterval = setInterval(updateScrapingStatus, 2000); // Poll every 2 seconds
}

function stopStatusPolling() {
    if (scrapingInterval) {
        clearInterval(scrapingInterval);
        scrapingInterval = null;
    }
}
