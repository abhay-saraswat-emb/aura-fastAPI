document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const modelSelect = document.getElementById('model-select');
    const systemPrompt = document.getElementById('system-prompt');
    const maxTokens = document.getElementById('max-tokens');
    const temperature = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperature-value');
    const pdfButton = document.getElementById('pdf-button');
    const ttsButton = document.getElementById('tts-button');
    const clearButton = document.getElementById('clear-button');
    const exportButton = document.getElementById('export-button');
    
    // PDF Modal Elements
    const pdfModal = document.getElementById('pdf-modal');
    const closeModal = document.querySelector('.close-modal');
    const pdfFileInput = document.getElementById('pdf-file');
    const fileNameDisplay = document.getElementById('file-name-display');
    const uploadPdfButton = document.getElementById('upload-pdf-button');
    const pdfStatus = document.getElementById('pdf-status');
    const internetSearch = document.getElementById('internet-search');

    
    // State variables
    let conversationHistory = [];
    let activePdfUrl = null;
    let isPdfMode = false;

    // Update temperature value display
    temperature.addEventListener('input', function() {
        temperatureValue.textContent = temperature.value;
    });

    // Send message when button is clicked
    sendButton.addEventListener('click', sendMessage);

    // Send message when Enter key is pressed (but allow Shift+Enter for new lines)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Handle PDF button click - Open the PDF modal
    pdfButton.addEventListener('click', function() {
        pdfModal.style.display = 'block';
    });
    
    // Close the modal when clicking the X
    closeModal.addEventListener('click', function() {
        pdfModal.style.display = 'none';
    });
    
    // Close the modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === pdfModal) {
            pdfModal.style.display = 'none';
        }
    });
    
    // Update the file name display when a file is selected
    pdfFileInput.addEventListener('change', function() {
        if (pdfFileInput.files.length > 0) {
            fileNameDisplay.textContent = pdfFileInput.files[0].name;
        } else {
            fileNameDisplay.textContent = 'Select PDF file';
        }
    });
    
    // Handle PDF upload
    uploadPdfButton.addEventListener('click', uploadPdf);
    
    // Handle TTS button click
    ttsButton.addEventListener('click', function() {
        alert('Text-to-Speech feature coming soon!');
    });
    
    // Handle clear button click
    if (clearButton) {
        clearButton.addEventListener('click', clearConversationHistory);
    }
    
    // Handle export button click
    if (exportButton) {
        exportButton.addEventListener('click', exportChat);
    }
    
    async function uploadPdf() {
        console.log("upload")
        const file = pdfFileInput.files[0];
        
        if (!file) {
            showPdfStatus('Please select a PDF file', 'error');
            return;
        }
        
        if (file.type !== 'application/pdf') {
            showPdfStatus('Selected file is not a PDF', 'error');
            return;
        }
        
        // Show loading status
        showPdfStatus('Uploading and analyzing PDF...', 'loading');
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('model', modelSelect.value);
        
        try {
            // Upload the PDF
            const response = await fetch('/pdf', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Failed to upload PDF');
            }
            
            const result = await response.json();
            
            // Store the PDF ID for future reference
            activePdfUrl = result.pdf_url;
            isPdfMode = true;
            
            // Show success message
            showPdfStatus(`PDF "${file.name}" uploaded and analyzed successfully!`, 'success');
            
            // Update UI to indicate PDF mode
            pdfButton.classList.add('pdf-active');
            pdfButton.innerHTML = 'PDF Analysis <span class="pdf-badge">Active</span>';
            
            // Close the modal after a delay
            setTimeout(() => {
                pdfModal.style.display = 'none';
                
                // Add a system message to indicate PDF mode
                addMessageToChat(`I've analyzed "${file.name}". You can now ask me questions about this PDF.`, 'system');
                
                // Reset conversation history for the new PDF
                conversationHistory = [];
            }, 2000);
            
        } catch (error) {
            console.error('PDF upload error:', error);
            showPdfStatus(`Error: ${error.message}`, 'error');
        }
    }
    
    function showPdfStatus(message, type) {
        pdfStatus.textContent = message;
        pdfStatus.className = '';
        pdfStatus.style.display = 'block';
        
        if (type === 'success') {
            pdfStatus.classList.add('status-success');
        } else if (type === 'error') {
            pdfStatus.classList.add('status-error');
        } else if (type === 'loading') {
            pdfStatus.classList.add('status-loading');
        }
    }
    
    // Function to exit PDF mode
    function exitPdfMode() {
        isPdfMode = false;
        activePdfUrl = null;
        pdfButton.classList.remove('pdf-active');
        pdfButton.textContent = 'PDF Analysis';
        
        // Reset conversation history
        conversationHistory = [];
        
        // Add a system message
        addMessageToChat('Exited PDF analysis mode. We are now having a regular conversation.', 'system');
    }

    // Function to send message and get response
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Check for exit PDF mode command
        if (isPdfMode && message.toLowerCase() === 'exit pdf mode') {
            addMessageToChat(message, 'user');
            exitPdfMode();
            userInput.value = '';
            return;
        }

        // Add user message to chat
        addMessageToChat(message, 'user');
        
        // Add user message to conversation history
        conversationHistory.push({
            role: "user",
            content: message
        });
        
        // Clear input field
        userInput.value = '';

        // Show thinking indicator
        const thinkingIndicator = addThinkingIndicator();

        try {
            // Get selected model and settings
            const model = modelSelect.value;
            const system = systemPrompt.value;
            const tokens = parseInt(maxTokens.value);
            const temp = parseFloat(temperature.value);

            // Prepare request data
            const requestData = {
                model: model,
                prompt: message,
                system_prompt: system,
                max_tokens: tokens,
                temperature: temp,
                conversation_history: conversationHistory
            };
            
            // Add PDF ID if in PDF mode
            if (isPdfMode && activePdfUrl) {
                requestData.pdf_url = activePdfUrl;
                requestData.pdf_mode = true;
            }

            // Send API request
            let apiEndpoint = '/chatbot/';
            if (isPdfMode) {
                apiEndpoint = '/chatbot/pdf-chat';
            } else if (internetSearch.checked) {
                apiEndpoint = '/search/';
            }
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            // Remove thinking indicator
            thinkingIndicator.remove();

            if (response.ok) {
                // Handle streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let responseText = '';

                // Create message container for AI response
                const messageElement = document.createElement('div');
                messageElement.className = 'message system';
                
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                
                const paragraph = document.createElement('p');
                messageContent.appendChild(paragraph);
                messageElement.appendChild(messageContent);
                chatMessages.appendChild(messageElement);

                // Process the stream
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    responseText += chunk;
                    paragraph.innerHTML = marked.parse(responseText);
                    
                    // Scroll to bottom as new content arrives
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
                
                // Add AI response to conversation history
                conversationHistory.push({
                    role: "assistant",
                    content: responseText
                });
                
                // Add copy button for the response
                const copyButton = document.createElement('button');
                copyButton.className = 'copy-button';
                copyButton.innerHTML = '📋';
                copyButton.title = 'Copy message';
                copyButton.addEventListener('click', function() {
                    navigator.clipboard.writeText(responseText).then(function() {
                        // Show copied confirmation
                        copyButton.innerHTML = '✓';
                        setTimeout(() => {
                            copyButton.innerHTML = '📋';
                        }, 2000);
                    });
                });
                messageContent.appendChild(copyButton);
            } else {
                // Handle error
                addMessageToChat(`Error: ${response.statusText}`, 'system');
            }
        } catch (error) {
            // Remove thinking indicator
            thinkingIndicator.remove();
            
            // Display error message
            addMessageToChat(`An error occurred: ${error.message}`, 'system');
        }

        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to add a message to the chat
    function addMessageToChat(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const paragraph = document.createElement('p');
        paragraph.innerHTML = marked.parse(message);
        
        messageContent.appendChild(paragraph);
        
        // Add copy button for system messages
        if (sender === 'system') {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.innerHTML = '📋';
            copyButton.title = 'Copy message';
            copyButton.addEventListener('click', function() {
                navigator.clipboard.writeText(message).then(function() {
                    // Show copied confirmation
                    copyButton.innerHTML = '✓';
                    setTimeout(() => {
                        copyButton.innerHTML = '📋';
                    }, 2000);
                });
            });
            messageContent.appendChild(copyButton);
        }
        
        messageElement.appendChild(messageContent);
        chatMessages.appendChild(messageElement);
        
        // Scroll to the new message
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageElement;
    }

    // Function to add thinking indicator
    function addThinkingIndicator() {
        const messageElement = document.createElement('div');
        messageElement.className = 'message system thinking';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const paragraph = document.createElement('p');
        paragraph.textContent = 'Thinking...';
        
        messageContent.appendChild(paragraph);
        messageElement.appendChild(messageContent);
        chatMessages.appendChild(messageElement);
        
        // Scroll to the thinking indicator
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageElement;
    }
    
    // Function to clear conversation history
    function clearConversationHistory() {
        conversationHistory = [];
        
        // If in PDF mode, also exit PDF mode
        if (isPdfMode) {
            exitPdfMode();
        }
        
        // Clear chat messages except for the initial greeting
        while (chatMessages.children.length > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }
    }

    // Load user preferences
    function loadUserPreferences() {
        const savedModel = localStorage.getItem('auraModel');
        const savedSystemPrompt = localStorage.getItem('auraSystemPrompt');
        const savedMaxTokens = localStorage.getItem('auraMaxTokens');
        const savedTemperature = localStorage.getItem('auraTemperature');
        const savedInternetSearch = localStorage.getItem('auraInternetSearch');
        if (savedInternetSearch === 'true') internetSearch.checked = true;
        
        if (savedModel) modelSelect.value = savedModel;
        if (savedSystemPrompt) systemPrompt.value = savedSystemPrompt;
        if (savedMaxTokens) maxTokens.value = savedMaxTokens;
        if (savedTemperature) {
            temperature.value = savedTemperature;
            temperatureValue.textContent = savedTemperature;
        }
    }

    // Save user preferences
    modelSelect.addEventListener('change', function() {
        localStorage.setItem('auraModel', modelSelect.value);
    });

    systemPrompt.addEventListener('blur', function() {
        localStorage.setItem('auraSystemPrompt', systemPrompt.value);
    });

    maxTokens.addEventListener('change', function() {
        localStorage.setItem('auraMaxTokens', maxTokens.value);
    });

    temperature.addEventListener('change', function() {
        localStorage.setItem('auraTemperature', temperature.value);
    });

    internetSearch.addEventListener('change', function () {
        localStorage.setItem('auraInternetSearch', internetSearch.checked);
    });

    // Function to export chat
    function exportChat() {
        let chatText = '';
        const messages = chatMessages.querySelectorAll('.message');
        
        messages.forEach(message => {
            const isUser = message.classList.contains('user');
            const text = message.querySelector('p').textContent;
            chatText += `${isUser ? 'You' : 'Aura'}: ${text}\n\n`;
        });
        
        // Create download link
        const blob = new Blob([chatText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `aura-chat-${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Initialize the app - only load preferences, not conversation history
    loadUserPreferences();
});

if (internetSearch.checked) {
    addMessageToChat("Internet search is enabled. I'm pulling real-time data.", "system");
}