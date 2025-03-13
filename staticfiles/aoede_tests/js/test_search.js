document.addEventListener('DOMContentLoaded', () => {
    const searchButton = document.querySelector('.search-button');
    const clearButton = document.querySelector('.results-clear');
    const resultsOutput = document.querySelector('.results-output');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Clear results
    clearButton.addEventListener('click', () => {
        resultsOutput.innerHTML = '';
    });

    // Handle search
    searchButton.addEventListener('click', async () => {
        const trackName = document.getElementById('search-track-name').value;
        const artistName = document.getElementById('search-artist-name').value;

        if (!trackName || !artistName) {
            resultsOutput.innerHTML = `
                <div class="error-message">
                    Please enter both track name and artist name
                </div>
            `;
            return;
        }

        try {
            // Show loading state
            searchButton.disabled = true;
            searchButton.innerHTML = '<span class="spinner"></span> Searching...';
            resultsOutput.innerHTML = '<div class="info-message">Searching...</div>';

            // Make the search request
            const response = await fetch('/tests/run-test/song_search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    track_name: trackName,
                    artist_name: artistName
                })
            });

            const data = await response.json();

            // Format and display results
            let resultsHtml = '';

            if (data.success) {
                resultsHtml = `
                    <div class="success-message">
                        <h3>Search Results</h3>
                        <div class="search-stats">
                            <div>Duration: ${data.duration}ms</div>
                            ${data.test_output ? `<div>Tests Run: ${data.test_output.tests_run || 0}</div>` : ''}
                        </div>
                        ${formatSearchResults(data)}
                    </div>
                `;
            } else {
                resultsHtml = `
                    <div class="error-message">
                        <h3>Search Failed</h3>
                        <p>${data.error || 'An unknown error occurred'}</p>
                    </div>
                `;
            }

            resultsOutput.innerHTML = resultsHtml;

        } catch (error) {
            resultsOutput.innerHTML = `
                <div class="error-message">
                    <h3>Error</h3>
                    <p>${error.message}</p>
                </div>
            `;
        } finally {
            // Reset button state
            searchButton.disabled = false;
            searchButton.textContent = 'Run Search Test';
        }
    });

    // Helper function to format search results
    function formatSearchResults(data) {
        if (!data.test_output) return '<p>No results found</p>';

        let html = '<div class="search-results">';

        // Format Spotify results
        if (data.test_output.spotify) {
            html += `
                <div class="platform-results">
                    <h4>Spotify Results</h4>
                    <div class="result-details">
                        ${formatPlatformResults(data.test_output.spotify)}
                    </div>
                </div>
            `;
        }

        // Format Apple Music results
        if (data.test_output.apple_music) {
            html += `
                <div class="platform-results">
                    <h4>Apple Music Results</h4>
                    <div class="result-details">
                        ${formatPlatformResults(data.test_output.apple_music)}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    function formatPlatformResults(results) {
        if (results.success) {
            return `
                <div class="success-details">
                    <div>Status: <span class="badge badge-success">Success</span></div>
                    ${results.track_id ? `<div>Track ID: ${results.track_id}</div>` : ''}
                    ${results.details ? `<pre>${results.details}</pre>` : ''}
                </div>
            `;
        } else {
            return `
                <div class="error-details">
                    <div>Status: <span class="badge badge-error">Failed</span></div>
                    <div>Error: ${results.error || 'Unknown error'}</div>
                </div>
            `;
        }
    }

    // Add styles for results
    const style = document.createElement('style');
    style.textContent = `
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .success-message, .error-message, .info-message {
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }

        .success-message {
            background-color: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
        }

        .error-message {
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .info-message {
            background-color: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
        }

        .search-stats {
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
            font-size: 0.9rem;
            color: #666;
        }

        .platform-results {
            margin-bottom: 1.5rem;
        }

        .platform-results h4 {
            margin-bottom: 0.5rem;
            color: #333;
        }

        .result-details {
            background: #fff;
            padding: 1rem;
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 4px;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .badge-success {
            background-color: rgba(34, 197, 94, 0.1);
            color: rgb(34, 197, 94);
        }

        .badge-error {
            background-color: rgba(239, 68, 68, 0.1);
            color: rgb(239, 68, 68);
        }

        pre {
            background: #f5f5f5;
            padding: 0.5rem;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }
    `;
    document.head.appendChild(style);
}); 
