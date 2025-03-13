class TestRunner {
    constructor() {
        this.runButtons = document.querySelectorAll('.aoede-run-test');
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.runButtons.forEach(button => {
            button.addEventListener('click', (e) => this.runTest(e));
        });
    }

    async runTest(event) {
        const button = event.currentTarget;
        const testSuite = button.dataset.testSuite;
        
        if (!testSuite) {
            testConsole.error('No test suite specified');
            return;
        }

        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span> Running...';
        
        try {
            testConsole.info(`Starting test suite: ${testSuite}`);
            
            const response = await fetch(`/tests/run-test/${testSuite}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const result = await response.json();
            
            if (response.ok) {
                if (result.success) {
                    testConsole.success(`Test suite ${testSuite} completed successfully`);
                    if (result.details) {
                        testConsole.info('Test Details:');
                        testConsole.info(result.details);
                    }
                } else {
                    testConsole.error(`Test suite ${testSuite} failed`);
                    if (result.error) {
                        testConsole.error(result.error);
                    }
                }
            } else {
                throw new Error(result.error || 'Unknown error occurred');
            }
        } catch (error) {
            testConsole.error(`Error running test suite ${testSuite}: ${error.message}`);
        } finally {
            button.disabled = false;
            button.textContent = 'Run Test';
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }
}

// Create a global instance
window.testRunner = new TestRunner(); 
