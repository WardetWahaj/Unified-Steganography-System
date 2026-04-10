// Unified Steganography System - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            // Add active to clicked
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Password field toggle based on encryption checkbox
    setupEncryptionToggle('hide-file');
    setupEncryptionToggle('extract-file');
    setupEncryptionToggle('hide-message');
    setupEncryptionToggle('extract-message');
    
    // Direct handler for hide-file encryption method
    const hideFileRadios = document.querySelectorAll('input[name="encryptionMethod"]');
    const passwordGroup = document.getElementById('passwordGroup');
    const hidePasswordInput = document.getElementById('hidePassword');
    
    console.log(`[INIT] Found ${hideFileRadios.length} encryption radios for hide-file`);
    
    if (hideFileRadios.length > 0 && passwordGroup) {
        hideFileRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                console.log(`[RADIO-CHANGE] hide-file encryption changed to: ${this.value}`);
                if (this.value === 'rsa') {
                    console.log(`[ACTION] Hiding password group`);
                    passwordGroup.style.display = 'none';
                    if (hidePasswordInput) hidePasswordInput.value = '';
                } else {
                    console.log(`[ACTION] Showing password group`);
                    passwordGroup.style.display = 'block';
                }
            });
        });
        
        // Initialize password visibility on page load
        const checkedRadio = document.querySelector('input[name="encryptionMethod"]:checked');
        if (checkedRadio && checkedRadio.value === 'rsa') {
            passwordGroup.style.display = 'none';
            console.log('[INIT] RSA is pre-selected, hiding password group');
        }
    }

    
    // Form handlers
    setupFormHandler('hide-file', handleHideFile);
    setupFormHandler('extract-file', handleExtractFile);
    setupFormHandler('hide-message', handleHideMessage);
    setupFormHandler('extract-message', handleExtractMessage);
    
    // Generate keys button
    document.getElementById('generate-keys-btn').addEventListener('click', generateKeys);
});

function setupEncryptionToggle(formPrefix) {
    console.log(`[DEBUG] setupEncryptionToggle called for: ${formPrefix}`);
    
    // Map form prefix to specific element IDs
    const config = {
        'hide-file': {
            radioName: 'encryptionMethod',
            passwordInputId: 'hidePassword',
            passwordGroupId: 'passwordGroup'
        },
        'hide-message': {
            radioName: 'messageEncryptionMethod',
            passwordInputId: 'messagePassword',
            passwordGroupId: 'messagePasswordGroup'
        },
        'extract-file': {
            radioName: 'extractEncryptionMethod',
            passwordInputId: 'extractPassword',
            passwordGroupId: 'extractPasswordGroup'
        },
        'extract-message': {
            radioName: 'extractMessageEncryptionMethod',
            passwordInputId: 'extractMessagePassword',
            passwordGroupId: 'extractMessagePasswordGroup'
        }
    };
    
    const cfg = config[formPrefix];
    if (!cfg) {
        console.log(`[DEBUG] No config found for ${formPrefix}`);
        return;
    }
    
    const radioButtons = document.querySelectorAll(`input[name="${cfg.radioName}"]`);
    const passwordInput = document.getElementById(cfg.passwordInputId);
    const passwordGroup = document.getElementById(cfg.passwordGroupId);
    
    console.log(`[DEBUG] ${formPrefix}: radioButtons=${radioButtons.length}, passwordInput=${passwordInput ? 'FOUND' : 'NOT FOUND'}, passwordGroup=${passwordGroup ? 'FOUND' : 'NOT FOUND'}`);
    
    if (!radioButtons.length || !passwordInput || !passwordGroup) {
        console.log(`[DEBUG] ${formPrefix}: Missing required elements, returning`);
        return;
    }
    
    // Function to update password visibility based on selected encryption
    function updatePasswordVisibility() {
        const checkedRadio = document.querySelector(`input[name="${cfg.radioName}"]:checked`);
        const selectedMethod = checkedRadio ? checkedRadio.value : 'hybrid';
        
        console.log(`[DEBUG] ${formPrefix}: updatePasswordVisibility - selected method: ${selectedMethod}`);
        
        if (selectedMethod === 'rsa') {
            console.log(`[DEBUG] ${formPrefix}: RSA selected - HIDING password group`);
            passwordGroup.style.display = 'none';
            passwordInput.value = '';
            passwordInput.required = false;
        } else {
            console.log(`[DEBUG] ${formPrefix}: ${selectedMethod} selected - SHOWING password group`);
            passwordGroup.style.display = 'block';
            passwordInput.required = true;
        }
    }
    
    // Add click listeners to all radio buttons
    radioButtons.forEach((radio, idx) => {
        console.log(`[DEBUG] ${formPrefix}: Adding listener to radio ${idx} (value=${radio.value})`);
        radio.addEventListener('change', function() {
            console.log(`[DEBUG] ${formPrefix}: Radio changed to ${this.value}`);
            updatePasswordVisibility();
        });
    });
    
    // Initialize on page load
    console.log(`[DEBUG] ${formPrefix}: Initializing password visibility`);
    updatePasswordVisibility();
}

function setupFormHandler(formId, handler) {
    const form = document.getElementById(`${formId}-form`);
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            handler(form);
        });
    }
}

function showLoading() {
    document.getElementById('loading').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('show');
}

function showResult(containerId, message, type = 'success', extraContent = '') {
    const resultDiv = document.getElementById(containerId);
    resultDiv.className = `result ${type}`;
    resultDiv.innerHTML = message + extraContent;
    resultDiv.style.display = 'block';
}

function hideResult(containerId) {
    const resultDiv = document.getElementById(containerId);
    resultDiv.style.display = 'none';
}

async function generateKeys() {
    if (!confirm('Generate new RSA keys? This will overwrite existing keys.')) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/generate-keys', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('RSA keys generated successfully!\n\n' +
                  'Public Key: ' + data.public_key + '\n' +
                  'Private Key: ' + data.private_key + '\n\n' +
                  'Keep your private key secure!');
            location.reload();
        } else {
            alert('Error generating keys: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function handleHideFile(form) {
    hideResult('hide-file-result');
    
    // Get form data directly - simpler approach
    const formData = new FormData(form);
    
    // Get password from form
    const password = formData.get('password') || '';
    
    // Get selected encryption method - safely
    const encryptionMethodElement = form.querySelector('input[name="encryptionMethod"]:checked');
    const encryptionMethod = encryptionMethodElement ? encryptionMethodElement.value : 'hybrid';
    console.log('[DEBUG] Hide File - Encryption method:', encryptionMethod);
    
    // Client-side validation: Check password requirement
    if ((encryptionMethod === 'password' || encryptionMethod === 'hybrid') && !password) {
        showResult('hide-file-result', '❌ Password is required for ' + encryptionMethod.toUpperCase() + ' encryption', 'error');
        return;
    }
    
    // Validate files exist
    if (!formData.get('secretFile') || !formData.get('coverFile')) {
        showResult('hide-file-result', '❌ Please select both secret file and cover file', 'error');
        return;
    }
    
    // Rename form fields to match backend parameters
    const secretFile = formData.get('secretFile');
    const coverFile = formData.get('coverFile');
    
    formData.delete('secretFile');
    formData.delete('coverFile');
    
    formData.append('secret_file', secretFile);
    formData.append('cover_file', coverFile);
    
    // Handle password based on encryption method
    // For RSA-only, remove password field entirely to prevent validation issues
    if (encryptionMethod === 'rsa') {
        if (formData.has('password')) {
            formData.delete('password');
        }
    } else {
        // For password/hybrid, keep the password but clear it if empty
        const passValue = formData.get('password') || '';
        formData.set('password', passValue);
    }
    
    formData.append('encryption_method', encryptionMethod);
    
    // Handle recipients - properly clean and format
    const recipientsSelect = document.getElementById('fileRecipients');
    let recipientsList = [];
    if (recipientsSelect) {
        try {
            const selectedOptions = Array.from(recipientsSelect.selectedOptions).map(opt => opt.value).filter(v => v !== '');
            recipientsList = selectedOptions;
        } catch (e) {
            console.error('[DEBUG] Error parsing file recipients:', e);
        }
    }
    // Remove original recipients field if it exists (from multi-select)
    if (formData.has('recipients')) {
        formData.delete('recipients');
    }
    // Add recipients as JSON string
    formData.append('recipients', JSON.stringify(recipientsList));
    
    console.log('[DEBUG] File - Encryption:', encryptionMethod, ', Recipients:', recipientsList);
    
    showLoading();
    
    try {
        const response = await fetch('/api/hide-file', {
            method: 'POST',
            body: formData
        });
        
        console.log(`[FETCH] Response status: ${response.status}`);
        
        const data = await response.json();
        console.log(`[FETCH] Response data:`, data);
        
        if (response.ok && data.success) {
            const downloadLink = `<a href="/api/download/${data.output_file}" class="download-link">📥 Download Stego File</a>`;
            showResult('hide-file-result', 
                      '✅ ' + data.message, 
                      'success', 
                      downloadLink);
            form.reset();
        } else {
            const errorMsg = data.error || data.detail || 'Unknown error occurred';
            console.log(`[FETCH] Error: ${errorMsg}`);
            showResult('hide-file-result', '❌ Error: ' + errorMsg, 'error');
        }
    } catch (error) {
        console.error(`[FETCH] Exception:`, error);
        showResult('hide-file-result', '❌ Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function handleExtractFile(form) {
    hideResult('extract-file-result');
    
    const formData = new FormData(form);
    const useEncryption = document.getElementById('use-encryption-extract-file').checked;
    formData.append('use_encryption', useEncryption);
    
    showLoading();
    
    try {
        const response = await fetch('/api/extract-file', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const downloadLink = `<a href="/api/download/${data.output_file}" class="download-link">📥 Download Extracted File</a>`;
            showResult('extract-file-result', 
                      '✅ ' + data.message, 
                      'success', 
                      downloadLink);
            form.reset();
        } else {
            showResult('extract-file-result', '❌ Error: ' + data.error, 'error');
        }
    } catch (error) {
        showResult('extract-file-result', '❌ Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function handleHideMessage(form) {
    hideResult('hide-message-result');
    
    // Get form data directly - simpler approach
    const formData = new FormData(form);
    
    // Get message and password from form
    const message = formData.get('message') || '';
    const password = formData.get('password') || '';
    
    if (!message) {
        showResult('hide-message-result', '❌ Please enter a message', 'error');
        return;
    }
    
    if (!formData.get('coverMedia')) {
        showResult('hide-message-result', '❌ Please select cover media', 'error');
        return;
    }
    
    // Get selected encryption method - safely
    const encryptionMethodElement = form.querySelector('input[name="messageEncryptionMethod"]:checked');
    const encryptionMethod = encryptionMethodElement ? encryptionMethodElement.value : 'hybrid';
    console.log('[DEBUG] Hide Message - Encryption method:', encryptionMethod);
    
    // Client-side validation: Check password requirement
    if ((encryptionMethod === 'password' || encryptionMethod === 'hybrid') && !password) {
        showResult('hide-message-result', '❌ Password is required for ' + encryptionMethod.toUpperCase() + ' encryption', 'error');
        return;
    }
    
    // Rename cover file field to match backend parameter
    const coverMedia = formData.get('coverMedia');
    formData.delete('coverMedia');
    formData.append('cover_file', coverMedia);
    
    // Handle password based on encryption method
    // For RSA-only, remove password field entirely to prevent validation issues
    if (encryptionMethod === 'rsa') {
        if (formData.has('password')) {
            formData.delete('password');
        }
    } else {
        // For password/hybrid, keep the password but ensure it's set
        const passValue = password || '';
        formData.set('password', passValue);
    }
    
    formData.append('encryption_method', encryptionMethod);
    
    // Handle recipients - properly clean and format
    const recipientsSelect = document.getElementById('messageRecipients');
    let recipientsList = [];
    if (recipientsSelect) {
        try {
            const selectedOptions = Array.from(recipientsSelect.selectedOptions).map(opt => opt.value).filter(v => v !== '');
            recipientsList = selectedOptions;
        } catch (e) {
            console.error('[DEBUG] Error parsing recipients:', e);
        }
    }
    // Remove original recipients field if it exists (from multi-select)
    if (formData.has('recipients')) {
        formData.delete('recipients');
    }
    // Add recipients as JSON string
    formData.append('recipients', JSON.stringify(recipientsList));
    
    console.log('[DEBUG] Message - Encryption:', encryptionMethod, ', Recipients:', recipientsList);
    
    showLoading();
    
    try {
        const response = await fetch('/api/hide-message', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const downloadLink = `<a href="/api/download/${data.output_file}" class="download-link">📥 Download Stego File</a>`;
            showResult('hide-message-result', 
                      '✅ ' + data.message, 
                      'success', 
                      downloadLink);
            form.reset();
        } else {
            showResult('hide-message-result', '❌ Error: ' + data.error, 'error');
        }
    } catch (error) {
        showResult('hide-message-result', '❌ Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function handleExtractMessage(form) {
    hideResult('extract-message-result');
    
    const formData = new FormData(form);
    const useEncryption = document.getElementById('use-encryption-extract-message').checked;
    formData.append('use_encryption', useEncryption);
    
    showLoading();
    
    try {
        const response = await fetch('/api/extract-message', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const messageBox = `<div class="message-box"><strong>Extracted Message:</strong><br>${escapeHtml(data.extracted_message)}</div>`;
            showResult('extract-message-result', 
                      '✅ ' + data.message, 
                      'success', 
                      messageBox);
            form.reset();
        } else {
            showResult('extract-message-result', '❌ Error: ' + data.error, 'error');
        }
    } catch (error) {
        showResult('extract-message-result', '❌ Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
