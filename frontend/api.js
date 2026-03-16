/* =====================================================
   ASK AI - API Service with Abort Support
   Authors: Annor Prince & Yeboah Collins
   ===================================================== */

const API = {
  // Store active abort controllers
  activeControllers: new Map(),
  
  // Create abort controller for a request
  createAbortController: (requestId) => {
    const controller = new AbortController();
    API.activeControllers.set(requestId, controller);
    return controller;
  },
  
  // Abort a specific request
  abortRequest: (requestId) => {
    const controller = API.activeControllers.get(requestId);
    if (controller) {
      controller.abort();
      API.activeControllers.delete(requestId);
      console.log(`🛑 Request ${requestId} aborted`);
      return true;
    }
    return false;
  },
  
  // Abort all active requests
  abortAllRequests: () => {
    API.activeControllers.forEach((controller, id) => {
      controller.abort();
    });
    API.activeControllers.clear();
    console.log('🛑 All requests aborted');
  },
  
  // Check if request was aborted
  isAborted: (error) => {
    return error.name === 'AbortError';
  },
  
  // Chat with AI (with abort support)
  analyzeText: async (text, conversationHistory = [], attachment = null, requestId = null) => {
    const controller = requestId ? API.createAbortController(requestId) : null;
    
    try {
      const body = { text, conversation_history: conversationHistory };
      if (attachment) body.attachment = attachment;
      
      const res = await fetch(`${CONFIG.BACKEND_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller?.signal,
      });
      
      if (requestId) API.activeControllers.delete(requestId);
      return res.json();
    } catch (error) {
      if (requestId) API.activeControllers.delete(requestId);
      throw error;
    }
  },
  
  // Upload and process document
  uploadDocument: async (fileData) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: fileData }),
    });
    return res.json();
  },
  
  // Get supported formats
  getSupportedFormats: async () => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/supported-formats`);
    return res.json();
  },
  
  // Authentication - Login
  login: async (email, password) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return res.json();
  },
  
  // Authentication - Register
  register: async (username, email, password) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });
    return res.json();
  },
  
  // Update Profile
  updateProfile: async (originalEmail, name, newEmail, currentPassword, newPassword) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/update-profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ originalEmail, name, newEmail, currentPassword, newPassword }),
    });
    return res.json();
  },
  
  // Delete Account
  deleteAccount: async (email, password) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/delete-account`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return res.json();
  },
  
  // Chat management - Load chats
  loadChats: async (userId) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/chats/load?user_id=${userId}`);
    return res.json();
  },
  
  // Chat management - Save chat
  saveChat: async (userId, chatData) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/chats/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, chat_data: chatData }),
    });
    return res.json();
  },
  
  // Password recovery - Check email
  checkEmail: async (email) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/check-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    return res.json();
  },
  
  // Password recovery - Reset password
  resetPassword: async (email, new_password) => {
    const res = await fetch(`${CONFIG.BACKEND_URL}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, new_password }),
    });
    return res.json();
  },
  
  // Transcribe audio (using ASR skill - would need backend support)
  transcribeAudio: async (audioBase64) => {
    // This would need to be implemented on the backend
    // For now, we'll use the browser's Speech Recognition API
    // But this endpoint is prepared for future server-side transcription
    const res = await fetch(`${CONFIG.BACKEND_URL}/transcribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audio: audioBase64 }),
    }).catch(() => ({ ok: false }));
    
    if (!res.ok) {
      return { success: false, error: 'Transcription not available' };
    }
    return res.json();
  },
};
