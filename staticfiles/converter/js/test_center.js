document.addEventListener('DOMContentLoaded', function() {
    const testButtons = document.querySelectorAll('[data-test-suite]');
    const testHistory = document.querySelector('.aoede-test-history');
    let testHistoryItems = [];
    
    function formatJson(obj) {
        return JSON.stringify(obj, null, 2)
            .replace(/"([^"]+)":/g, '<span class="aoede-json-key">"$1"</span>:')
            .replace(/"([^"]+)"/g, '<span class="aoede-json-string">"$1"</span>')
            .replace(/\b(\d+)\b/g, '<span class="aoede-json-number">$1</span>')
            .replace(/\b(true|false)\b/g, '<span class="aoede-json-boolean">$1</span>')
            .replace(/\bnull\b/g, '<span class="aoede-json-null">null</span>');
    }
    
    function addToTestHistory(testSuite, success, results) {
        const time = new Date().toLocaleTimeString();
        const historyItem = {
            time,
            testSuite,
            success,
            results
        };
        
        testHistoryItems.unshift(historyItem);
        if (testHistoryItems.length > 10) testHistoryItems.pop();
        
        updateTestHistory();
    }
    
    function updateTestHistory() {
        let html = '<h3>Recent Test Runs</h3>';
        
        testHistoryItems.forEach(item => {
            html += `
                <div class="aoede-test-history-item">
                    <div class="aoede-test-metadata">
                        <span class="aoede-test-history-time">${item.time}</span>
                        <span class="aoede-badge aoede-badge-${item.success ? 'success' : 'failure'}">
                            ${item.success ? 'SUCCESS' : 'FAILURE'}
                        </span>
                        <span class="aoede-test-metadata-label">${item.testSuite}</span>
                    </div>
                </div>
            `;
        });
        
        testHistory.innerHTML = html;
    }
    
    function getTestParameters(testSuite) {
        const params = {};
        
        switch (testSuite) {
            case 'song_search':
                params.track_name = document.getElementById('search-track-name').value;
                params.artist_name = document.getElementById('search-artist-name').value;
                break;
                
            case 'playlist_creation':
                params.name = document.getElementById('playlist-name').value;
                params.description = document.getElementById('playlist-description').value;
                params.track_ids = document.getElementById('playlist-tracks').value.split(',');
                break;
                
            case 'apple_auth':
                params.auth_type = document.getElementById('apple-auth-type').value;
                break;
                
            case 'spotify_auth':
                params.auth_type = document.getElementById('spotify-auth-type').value;
                break;
        }
        
        return params;
    }
    
    function displayTestMetadata(result) {
        let metadata = '<div class="aoede-test-metadata">';
        
        if (result.duration) {
            metadata += `
                <div class="aoede-test-metadata-item">
                    <span class="aoede-test-metadata-label">Duration:</span>
                    <span>${result.duration}ms</span>
                </div>
            `;
        }
        
        if (result.timestamp) {
            metadata += `
                <div class="aoede-test-metadata-item">
                    <span class="aoede-test-metadata-label">Time:</span>
                    <span>${new Date(result.timestamp).toLocaleTimeString()}</span>
                </div>
            `;
        }
        
        metadata += '</div>';
        return metadata;
    }
    
    function displayDetailedResults(result) {
        let details = '';
        
        // Display test output
        if (result.details) {
            details += `
                <div class="aoede-test-details">
                    <h4>Test Output</h4>
                    <pre>${result.details}</pre>
                </div>
            `;
        }
        
        // Display API response data if available
        if (result.response_data) {
            details += `
                <div class="aoede-test-details">
                    <h4>API Response</h4>
                    <div class="aoede-json-view">${formatJson(result.response_data)}</div>
                </div>
            `;
        }
        
        // Display extracted data if available
        if (result.extracted_data) {
            details += `
                <div class="aoede-test-details">
                    <h4>Extracted Data</h4>
                    <div class="aoede-json-view">${formatJson(result.extracted_data)}</div>
                </div>
            `;
        }
        
        return details;
    }
    
    testButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const testSuite = this.dataset.testSuite;
            const resultContainer = this.closest('.aoede-grid-item').querySelector('.aoede-test-results');
            const params = getTestParameters(testSuite);
            
            try {
                // Show loading state
                this.classList.add('loading');
                this.disabled = true;
                
                // Run the test
                const response = await fetch(`/run-test/${testSuite}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify(params)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Process test results
                    let resultsHtml = '<div class="aoede-test-results-container">';
                    
                    data.results.forEach(result => {
                        const statusClass = result.passed ? 'success' : 'failure';
                        resultsHtml += `
                            <div class="aoede-test-result ${statusClass}">
                                <h4>${result.name}</h4>
                                <div class="aoede-test-status">
                                    <span class="aoede-badge aoede-badge-${statusClass}">
                                        ${result.passed ? 'PASSED' : 'FAILED'}
                                    </span>
                                </div>
                                ${displayTestMetadata(result)}
                                ${displayDetailedResults(result)}
                            </div>
                        `;
                    });
                    
                    resultsHtml += '</div>';
                    resultContainer.innerHTML = resultsHtml;
                    
                    // Add to test history
                    addToTestHistory(testSuite, true, data.results);
                } else {
                    // Show error
                    resultContainer.innerHTML = `
                        <div class="aoede-test-error">
                            <span class="aoede-badge aoede-badge-error">ERROR</span>
                            <pre>${data.error}</pre>
                        </div>
                    `;
                    
                    // Add to test history
                    addToTestHistory(testSuite, false, [{
                        name: testSuite,
                        error: data.error
                    }]);
                }
            } catch (error) {
                // Show error
                resultContainer.innerHTML = `
                    <div class="aoede-test-error">
                        <span class="aoede-badge aoede-badge-error">ERROR</span>
                        <pre>Failed to run test: ${error.message}</pre>
                    </div>
                `;
                
                // Add to test history
                addToTestHistory(testSuite, false, [{
                    name: testSuite,
                    error: error.message
                }]);
            } finally {
                // Reset button state
                this.classList.remove('loading');
                this.disabled = false;
            }
        });
    });
}); 
