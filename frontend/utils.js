/* =====================================================
   ASK AI - Utility Functions
   Authors: Annor Prince & Yeboah Collins
   ===================================================== */

const Utils = {
  // Generate unique ID
  generateId: () => `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  
  // Check if mobile device
  isMobile: () => window.innerWidth < 768,
  
  // Format file size
  formatFileSize: (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  },
  
  // Format duration (seconds to mm:ss)
  formatDuration: (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  },
  
  // Get file extension
  getFileExtension: (filename) => {
    return filename.split('.').pop().toLowerCase();
  },
  
  // Get file category
  getFileCategory: (filename) => {
    const ext = Utils.getFileExtension(filename);
    if (['pdf'].includes(ext)) return 'pdf';
    if (['docx', 'doc'].includes(ext)) return 'docx';
    if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return 'image';
    if (['txt', 'md', 'csv'].includes(ext)) return 'txt';
    return 'unknown';
  },
  
  // Truncate text
  truncateText: (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  },
  
  // Format date
  formatDate: (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) return 'Just now';
    // Less than 1 hour
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    // Less than 24 hours
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    // Less than 7 days
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
    
    return date.toLocaleDateString();
  },
  
  // Debounce function
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },
  
  // Throttle function
  throttle: (func, limit) => {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
  
  // Check if browser supports speech recognition
  supportsSpeechRecognition: () => {
    return 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
  },
  
  // Check if browser supports media recording
  supportsMediaRecording: () => {
    return 'MediaRecorder' in window && navigator.mediaDevices;
  },
  
  // Convert audio blob to base64
  audioBlobToBase64: async (blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  },
  
  // Parse markdown safely
  parseMarkdown: (text) => {
    if (typeof marked !== 'undefined') {
      return marked.parse(text);
    }
    // Fallback: basic markdown parsing
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  },
};
