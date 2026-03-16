/* =====================================================
   ASK AI - Configuration
   Authors: Annor Prince & Yeboah Collins
   ===================================================== */

const CONFIG = {
  // Backend API URL
  BACKEND_URL: 'https://med-ai-48yi.onrender.com/api',
  
  // EmailJS Configuration
  EMAILJS_SERVICE_ID: 'service_zjhyid5',
  EMAILJS_TEMPLATE_ID: 'template_vha29yp',
  EMAILJS_PUBLIC_KEY: 'lTUvDRylLKuYhqt9o',
  
  // App Info
  APP_NAME: 'ASK AI',
  DEVELOPERS: ['Annor Prince', 'Yeboah Collins'],
  
  // File Upload Settings
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  SUPPORTED_FORMATS: {
    pdf: { icon: '📄', name: 'PDF Document', extensions: ['pdf'] },
    docx: { icon: '📝', name: 'Word Document', extensions: ['docx', 'doc'] },
    txt: { icon: '📃', name: 'Text File', extensions: ['txt', 'md', 'csv'] },
    image: { icon: '🖼️', name: 'Image', extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp'] },
  },
  
  // Voice Recording Settings
  MAX_VOICE_DURATION: 60, // seconds
  VOICE_MIME_TYPE: 'audio/webm',
  
  // Chat Settings
  MAX_CONVERSATION_HISTORY: 10,
  TYPING_INDICATOR_DELAY: 500,
};

// Initialize EmailJS
if (window.emailjs) {
  window.emailjs.init(CONFIG.EMAILJS_PUBLIC_KEY);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
}
