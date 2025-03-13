class TestConsole {
    constructor() {
        this.output = document.querySelector('.aoede-console-output');
        this.clearButton = document.querySelector('.aoede-console-clear');
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => this.clear());
        }
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `aoede-console-entry aoede-console-${type}`;
        
        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'aoede-console-timestamp';
        timestampSpan.textContent = `[${timestamp}] `;
        
        const messageSpan = document.createElement('span');
        messageSpan.className = 'aoede-console-message';
        
        if (typeof message === 'object') {
            messageSpan.textContent = JSON.stringify(message, null, 2);
        } else {
            messageSpan.textContent = message;
        }
        
        logEntry.appendChild(timestampSpan);
        logEntry.appendChild(messageSpan);
        
        if (this.output) {
            this.output.appendChild(logEntry);
            this.output.scrollTop = this.output.scrollHeight;
        }
    }

    info(message) {
        this.log(message, 'info');
    }

    success(message) {
        this.log(message, 'success');
    }

    error(message) {
        this.log(message, 'error');
    }

    warn(message) {
        this.log(message, 'warning');
    }

    clear() {
        if (this.output) {
            this.output.innerHTML = '';
        }
    }
}

// Create a global instance
window.testConsole = new TestConsole(); 
