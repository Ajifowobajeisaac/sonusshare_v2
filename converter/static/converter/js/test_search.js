document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const testButtons = document.querySelectorAll('[data-test-suite]');
    const resultsContainer = document.querySelector('.aoede-test-results');

    function getTestParameters(testSuite) {
        switch (testSuite) {
            case 'song_search':
                return {
                    track_name: document.getElementById('search-track-name').value,
                    artist_name: document.getElementById('search-artist-name').value
                };
            default:
                return {};
        }
    }

    function displayTestResults(results) {
        const resultDiv = document.createElement('div');
        resultDiv.className = `aoede-test-result ${results.success ? 'success' : 'failure'}`;
        
        // Display test metadata
        const metadata = document.createElement('div');
        metadata.className = 'aoede-test-metadata';
        metadata.innerHTML = `
            <span class="aoede-badge ${results.success ? 'aoede-badge-success' : 'aoede-badge-error'}">
                ${results.success ? 'Success' : 'Failed'}
            </span>
            <span class="aoede-badge aoede-badge-info">
                Duration: ${results.duration}ms
            </span>
        `;
        
        // Display test details
        const details = document.createElement('div');
        details.className = 'aoede-test-details';
        
        if (results.test_output) {
            const outputPre = document.createElement('pre');
            outputPre.className = 'aoede-json-view';
            outputPre.textContent = JSON.stringify(results.test_output, null, 2);
            details.appendChild(outputPre);
        }
        
        resultDiv.appendChild(metadata);
        resultDiv.appendChild(details);
        
        // Add to results container
        resultsContainer.insertBefore(resultDiv, resultsContainer.firstChild);
        
        // Log to console
        if (results.success) {
            window.testConsole.success(`Test completed successfully in ${results.duration}ms`);
        } else {
            window.testConsole.error(`Test failed in ${results.duration}ms`);
        }
        
        if (results.test_output) {
            window.testConsole.info('Test output:');
            window.testConsole.log(results.test_output);
        }
    }

    testButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const testSuite = button.dataset.testSuite;
            const originalText = button.textContent;
            
            try {
                button.disabled = true;
                button.innerHTML = '<span class="aoede-spinner"></span> Running...';
                window.testConsole.info(`Starting ${testSuite} test...`);
                
                const parameters = getTestParameters(testSuite);
                window.testConsole.info('Test parameters:', parameters);
                
                const response = await fetch(`/run-test/${testSuite}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(parameters)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const results = await response.json();
                displayTestResults(results);
                
            } catch (error) {
                window.testConsole.error(`Error running test: ${error.message}`);
                const errorDiv = document.createElement('div');
                errorDiv.className = 'aoede-test-result failure';
                errorDiv.innerHTML = `
                    <div class="aoede-test-metadata">
                        <span class="aoede-badge aoede-badge-error">Error</span>
                    </div>
                    <div class="aoede-test-details">
                        <pre class="aoede-error-message">${error.message}</pre>
                    </div>
                `;
                resultsContainer.insertBefore(errorDiv, resultsContainer.firstChild);
            } finally {
                button.disabled = false;
                button.textContent = originalText;
            }
        });
    });
}); 
