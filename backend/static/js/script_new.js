// Unified Steganography System - JavaScript with User Authentication

let currentUser = null;

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    checkAuthStatus();
    
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Modal tab switching for auth
    const modalTabBtns = document.querySelectorAll('.modal-tab-btn');
    const modalTabPanes = document.querySelectorAll('.modal-tab-pane');
    
    modalTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modalTabBtns.forEach(b => b.classList.remove('active'));
            modalTabPanes.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Password field setup for encryption toggle
    setupEncryptionToggleForRadios('hide-file');
    setupEncryptionToggleForRadios('hide-message');
    setupEncryptionToggleForRadios('extract-file');
    setupEncryptionToggleForRadios('extract-message');
    
    // Direct handler for hide-file encryption method
    const hideFileRadios = document.querySelectorAll('input[name="encryptionMethod"]');
    const passwordGroup = document.getElementById('passwordGroup');
    const hidePasswordInput = document.getElementById('hidePassword');
    
    console.log(`[INIT] Found ${hideFileRadios.length} encryption radios for hide-file`);
    
    hideFileRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            console.log(`[RADIO-CHANGE] hide-file encryption changed to: ${this.value}`);
            if (this.value === 'rsa') {
                console.log(`[ACTION] Hiding password group`);
                passwordGroup.style.display = 'none';
                hidePasswordInput.value = '';
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

    
    // Form handlers
    setupFormHandler('hide-file', handleHideFile);
    setupFormHandler('extract-file', handleExtractFile);
    setupFormHandler('hide-message', handleHideMessage);
    setupFormHandler('extract-message', handleExtractMessage);
    
    // Authentication handlers
    document.getElementById('login-btn').addEventListener('click', openAuthModal);
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('signup-form').addEventListener('submit', handleSignup);
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('auth-modal');
        if (e.target === modal) {
            closeAuthModal();
        }
    });
});

// ============= Authentication Functions =============

function checkAuthStatus() {
    const userStr = localStorage.getItem('stego_user');
    if (userStr) {
        currentUser = JSON.parse(userStr);
        updateUserDisplay();
    }
}

function openAuthModal() {
    document.getElementById('auth-modal').style.display = 'block';
}

function closeAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

function updateUserDisplay() {
    const userDisplay = document.getElementById('user-display');
    const notLoggedIn = document.getElementById('not-logged-in');
    const keyIndicator = document.getElementById('user-keys-indicator');
    const keyInfoText = document.getElementById('key-info-text');
    
    if (currentUser) {
        userDisplay.style.display = 'flex';
        notLoggedIn.style.display = 'none';
        document.getElementById('current-username').textContent = '👤 ' + currentUser.username;
        
        keyIndicator.innerHTML = '<span class="status-badge success">✓ Keys Active</span>';
        keyInfoText.style.display = 'block';
    } else {
        userDisplay.style.display = 'none';
        notLoggedIn.style.display = 'block';
        keyIndicator.innerHTML = '<span class="status-badge pending">⏳ Login to activate keys</span>';
        keyInfoText.style.display = 'none';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');
    
    errorDiv.textContent = '';
    
    try {
        const response = await fetch('/api/user/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = { user_id: data.user_id, username: data.username };
            localStorage.setItem('stego_user', JSON.stringify(currentUser));
            updateUserDisplay();
            closeAuthModal();
            document.getElementById('login-form').reset();
            alert('✅ Login successful!');
        } else {
            errorDiv.textContent = '❌ ' + (data.error || 'Login failed');
        }
    } catch (error) {
        errorDiv.textContent = '❌ Error: ' + error.message;
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;
    const confirm = document.getElementById('signup-confirm').value;
    const errorDiv = document.getElementById('signup-error');
    
    errorDiv.textContent = '';
    
    if (password !== confirm) {
        errorDiv.textContent = '❌ Passwords do not match';
        return;
    }
    
    if (username.length < 3) {
        errorDiv.textContent = '❌ Username must be at least 3 characters';
        return;
    }
    
    if (password.length < 6) {
        errorDiv.textContent = '❌ Password must be at least 6 characters';
        return;
    }
    
    try {
        const response = await fetch('/api/user/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = { user_id: data.user_id, username: data.username };
            localStorage.setItem('stego_user', JSON.stringify(currentUser));
            updateUserDisplay();
            closeAuthModal();
            document.getElementById('signup-form').reset();
            alert('✅ Account created successfully! Your RSA keys have been generated and stored securely.');
        } else {
            errorDiv.textContent = '❌ ' + (data.error || 'Signup failed');
        }
    } catch (error) {
        errorDiv.textContent = '❌ Error: ' + error.message;
    }
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        currentUser = null;
        localStorage.removeItem('stego_user');
        updateUserDisplay();
        // Reset all forms
        document.querySelectorAll('form').forEach(f => f.reset());
        alert('✅ Logged out successfully');
    }
}

// ============= Encryption Toggle =============

// ============= Encryption Setup =============
function setupEncryptionToggleForRadios(formPrefix) {
    console.log(`[DEBUG] setupEncryptionToggleForRadios called for: ${formPrefix}`);
    
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

// ============= Keep old function for compatibility =============
function setupEncryptionToggle(formPrefix) {
    // This is kept for backward compatibility
    setupEncryptionToggleForRadios(formPrefix);
}

function updatePasswordGroup(checkbox, passwordGroup, passwordInput) {
    if (checkbox.checked) {
        passwordGroup.style.display = 'block';
        passwordInput.required = false;
    } else {
        passwordGroup.style.display = 'none';
        passwordInput.required = false;
    }
}

// ============= Form Handlers =============

function setupFormHandler(formId, handler) {
    const form = document.getElementById(`${formId}-form`);
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            if (!currentUser) {
                alert('⚠️ Please login first');
                openAuthModal();
                return;
            }
            
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

async function handleHideFile(form) {
    hideResult('hide-file-result');
    
    if (!currentUser) {
        showResult('hide-file-result', '❌ Please login first', 'error');
        return;
    }
    
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
    formData.append('user_id', currentUser.user_id);
    
    // Log FormData contents for debugging
    console.log('[DEBUG] FormData contents:');
    for (let pair of formData.entries()) {
        console.log(`  - ${pair[0]}: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
    }
    
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
                      '✅ ' + data.message + '<br><small>Signed with your private key</small>', 
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
    hideSignatureInfo();
    
    if (!currentUser) {
        showResult('extract-file-result', '❌ Please login first', 'error');
        return;
    }
    
    const formData = new FormData(form);
    const useEncryption = document.getElementById('use-encryption-extract-file').checked;
    const password = document.getElementById('password-extract-file').value || '';
    
    formData.append('use_encryption', useEncryption);
    if (password) formData.append('password', password);
    formData.append('user_id', currentUser.user_id);
    
    showLoading();
    
    try {
        const response = await fetch('/api/extract-file', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const downloadLink = `<a href="/api/download/${data.output_file}" class="download-link">📥 Download Extracted File</a>`;
            let resultMsg = '✅ ' + data.message;
            
            // Show signature verification if available
            if (data.metadata) {
                showSignatureInfo(data.metadata);
            }
            
            showResult('extract-file-result', resultMsg, 'success', downloadLink);
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
    
    if (!currentUser) {
        showResult('hide-message-result', '❌ Please login first', 'error');
        return;
    }
    
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
    formData.append('user_id', currentUser.user_id);
    
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
                      '✅ ' + data.message + '<br><small>Digitally signed with your key</small>', 
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
    hideMessageSignatureInfo();
    
    if (!currentUser) {
        showResult('extract-message-result', '❌ Please login first', 'error');
        return;
    }
    
    const formData = new FormData(form);
    const useEncryption = document.getElementById('use-encryption-extract-message').checked;
    const password = document.getElementById('password-extract-message').value || '';
    
    formData.append('use_encryption', useEncryption);
    if (password) formData.append('password', password);
    formData.append('user_id', currentUser.user_id);
    
    showLoading();
    
    try {
        const response = await fetch('/api/extract-message', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const messageBox = `<div class="message-box"><strong>📨 Extracted Message:</strong><br><br>${escapeHtml(data.extracted_message)}</div>`;
            let resultMsg = '✅ ' + data.message;
            
            // Show signature verification if available
            if (data.metadata) {
                showMessageSignatureInfo(data.metadata);
            }
            
            showResult('extract-message-result', resultMsg, 'success', messageBox);
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

// ============= Signature Verification Display =============

function showSignatureInfo(metadata) {
    const signatureInfo = document.getElementById('signature-info');
    
    if (metadata.creator_username) {
        document.getElementById('hidden-by-user').textContent = metadata.creator_username;
        document.getElementById('hidden-by-userid').textContent = metadata.creator_user_id;
        
        if (metadata.creator_public_key) {
            document.getElementById('creator-public-key').textContent = metadata.creator_public_key;
        }
        
        signatureInfo.style.display = 'block';
    }
}

function hideSignatureInfo() {
    document.getElementById('signature-info').style.display = 'none';
}

function showMessageSignatureInfo(metadata) {
    const signatureInfo = document.getElementById('message-signature-info');
    
    if (metadata.creator_username) {
        document.getElementById('message-from-user').textContent = metadata.creator_username + ' (ID: ' + metadata.creator_user_id + ')';
        signatureInfo.style.display = 'block';
    }
}

function hideMessageSignatureInfo() {
    document.getElementById('message-signature-info').style.display = 'none';
}

// ============= Utility Functions =============

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
