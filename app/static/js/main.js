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
    const chatScrollUp = document.getElementById('chat-scroll-up');
    const chatScrollDown = document.getElementById('chat-scroll-down');
    const chatScrollThumb = document.getElementById('chat-scroll-thumb');
    const scrollTrack = document.querySelector('.scroll-track');
    
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
    let isDragging = false;
    
    // Initialize custom scroller
    function updateChatScrollThumb() {
        const contentHeight = chatMessages.scrollHeight;
        const viewportHeight = chatMessages.clientHeight;
        const scrollRatio = viewportHeight / contentHeight;
        
        // Only show thumb if content is scrollable
        if (scrollRatio >= 1) {
            chatScrollThumb.style.display = 'none';
            return;
        }
        
        chatScrollThumb.style.display = 'block';
        const trackHeight = scrollTrack.clientHeight;
        const thumbHeight = Math.max(30, trackHeight * scrollRatio);
        chatScrollThumb.style.height = thumbHeight + 'px';
        
        const scrollPosition = chatMessages.scrollTop;
        const maxScroll = contentHeight - viewportHeight;
        const thumbPosition = (scrollPosition / maxScroll) * (trackHeight - thumbHeight);
        chatScrollThumb.style.top = thumbPosition + 'px';
    }
    
    // Set up custom scroller events
    chatScrollUp.addEventListener('click', () => {
        chatMessages.scrollBy({ top: -100, behavior: 'smooth' });
    });
    
    chatScrollDown.addEventListener('click', () => {
        chatMessages.scrollBy({ top: 100, behavior: 'smooth' });
    });
    
    chatScrollThumb.addEventListener('mousedown', (e) => {
        isDragging = true;
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const trackRect = scrollTrack.getBoundingClientRect();
        const thumbHeight = chatScrollThumb.clientHeight;
        const trackHeight = trackRect.height;
        
        let thumbPosition = e.clientY - trackRect.top - (thumbHeight / 2);
        thumbPosition = Math.max(0, Math.min(trackHeight - thumbHeight, thumbPosition));
        
        const contentHeight = chatMessages.scrollHeight;
        const viewportHeight = chatMessages.clientHeight;
        const maxScroll = contentHeight - viewportHeight;
        const scrollPosition = (thumbPosition / (trackHeight - thumbHeight)) * maxScroll;
        
        chatMessages.scrollTop = scrollPosition;
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
    
    chatMessages.addEventListener('scroll', updateChatScrollThumb);
    window.addEventListener('resize', updateChatScrollThumb);

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
        
        if (file.type == 'application/pdf') {
        }
        
        // Show loading status
        showPdfStatus('Uploading and analyzing file...', 'loading');
        
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
                throw new Error(errorText || 'Failed to upload file');
            }
            
            const result = await response.json();
            
            // Store the PDF ID for future reference
            activePdfUrl = result.pdf_url;
            isPdfMode = true;
            
            // Show success message
            showPdfStatus(`PDF "${file.name}" uploaded and analyzed successfully!`, 'success');
            
            // Update UI to indicate PDF mode
            pdfButton.classList.add('pdf-active');
            pdfButton.innerHTML = 'File <span class="pdf-badge">Active</span>';
            
            // Close the modal after a delay
            setTimeout(() => {
                pdfModal.style.display = 'none';
                
                // Add a system message to indicate file mode
                addMessageToChat(`I've analyzed "${file.name}". You can now ask me questions about this file.`, 'system');
                
                // Reset conversation history for the new file
                conversationHistory = [];
            }, 2000);
            
        } catch (error) {
            console.error('file upload error:', error);
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
        pdfButton.textContent = 'File';
        
        // Reset conversation history
        conversationHistory = [];
        
        // Add a system message
        addMessageToChat('Exited File mode. We are now having a regular conversation.', 'system');
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
                apiEndpoint = '/chatbot/file-chat';
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
        
        // Scroll to the new message with a slight delay to ensure rendering is complete
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
            updateChatScrollThumb();
        }, 10);
        
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
        
        // Scroll to the thinking indicator with a slight delay
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
            updateChatScrollThumb();
        }, 10);
        
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
    
    // Initialize the scroll thumb
    setTimeout(updateChatScrollThumb, 100);
});

if (internetSearch.checked) {
    addMessageToChat("Internet search is enabled. I'm pulling real-time data.", "system");
}

document.addEventListener("DOMContentLoaded", () => {
    // Example product data (optional dynamic render)
    const products = [
      {
        id: 1,
        title: "AI Assistant Pack",
        description: "Boost your workflow with this pre-configured AI tool pack.",
        price: "$19.99",
        image: "https://via.placeholder.com/300x150"
      },
      {
        id: 2,
        title: "TTS Plugin",
        description: "A sleek text-to-speech plugin for fast integration.",
        price: "$9.99",
        image: "https://via.placeholder.com/300x150"
      },
      {
        id: 3,
        title: "PDF Summarizer",
        description: "Summarize lengthy PDFs in seconds.",
        price: "$14.99",
        image: "https://via.placeholder.com/300x150"
      }
    ];
  
    const grid = document.querySelector(".marketplace-grid");
  
    // Dynamically render products
    if (grid && products.length) {
      products.forEach((product) => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.innerHTML = `
          <img src="${product.image}" class="product-image" alt="${product.title}" />
          <div class="product-title">${product.title}</div>
          <div class="product-description">${product.description}</div>
          <div class="product-actions">
            <span class="product-price">${product.price}</span>
            <button class="buy-button" data-id="${product.id}">Buy</button>
          </div>
        `;
        grid.appendChild(card);
      });
    }
  
    // Event delegation for Buy buttons
    document.body.addEventListener("click", (e) => {
      if (e.target.classList.contains("buy-button")) {
        const productId = e.target.dataset.id;
        const product = products.find(p => p.id == productId);
        if (product) {
          alert(`You bought "${product.title}" for ${product.price}`);
          // Later: Add to cart, trigger checkout modal, etc.
        }
      }
    });
  });

  document.body.addEventListener("click", (e) => {
    if (e.target.closest(".product-card") && !e.target.classList.contains("buy-button")) {
      const card = e.target.closest(".product-card");
      const title = card.querySelector(".product-title").textContent;
      const image = card.querySelector(".product-image").src;
      const description = card.querySelector(".product-description").textContent;
      const price = card.querySelector(".product-price").textContent;
  
      document.getElementById("modal-title").textContent = title;
      document.getElementById("modal-image").src = image;
      document.getElementById("modal-description").textContent = description;
      document.getElementById("modal-price").textContent = `Price: ${price}`;
  
      document.getElementById("product-modal").style.display = "block";
    }
  });
  


  document.addEventListener("DOMContentLoaded", () => {
    const products = [
      {
        id: 1,
        title: "AI Assistant Pack",
        description: "Boost your workflow with this pre-configured AI tool pack.",
        price: "$19.99",
        image: "https://via.placeholder.com/300x150"
      },
      {
        id: 2,
        title: "TTS Plugin",
        description: "A sleek text-to-speech plugin for fast integration.",
        price: "$9.99",
        image: "https://via.placeholder.com/300x150"
      },
      {
        id: 3,
        title: "PDF Summarizer",
        description: "Summarize lengthy PDFs in seconds.",
        price: "$14.99",
        image: "https://via.placeholder.com/300x150"
      }
    ];
  
    const grid = document.querySelector(".marketplace-grid");
  
    if (grid && products.length) {
      products.forEach((product) => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.dataset.id = product.id;
        card.innerHTML = `
          <img src="${product.image}" class="product-image" alt="${product.title}" />
          <div class="product-title">${product.title}</div>
          <div class="product-description">${product.description}</div>
          <div class="product-actions">
            <span class="product-price">${product.price}</span>
            <button class="publish-button" data-id="${product.id}">Publish</button>
          </div>
        `;
        grid.appendChild(card);
      });
    }
  
    const modal = document.getElementById("publish-modal");
    let selectedProductId = null;
  
    document.body.addEventListener("click", (e) => {
      if (e.target.classList.contains("publish-button")) {
        selectedProductId = e.target.dataset.id;
        modal.style.display = "block";
      }
  
      if (e.target.classList.contains("publish-option")) {
        const mode = e.target.dataset.mode;
        if (!selectedProductId) return;
  
        fetch('/api/publish', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ productId: selectedProductId, mode })
        })
          .then(res => res.json())
          .then(data => {
            alert(`Published as ${mode.toUpperCase()}: ${data.message || 'Success'}`);
          })
          .catch(err => {
            alert(`Failed to publish: ${err.message}`);
          })
          .finally(() => {
            modal.style.display = "none";
            selectedProductId = null;
          });
      }
  
      if (e.target.classList.contains("close-modal")) {
        modal.style.display = "none";
        selectedProductId = null;
      }
    });
  });
