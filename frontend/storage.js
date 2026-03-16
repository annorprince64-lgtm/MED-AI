/* =====================================================
   ASK AI - Storage Management
   Authors: Annor Prince & Yeboah Collins
   ===================================================== */

const Storage = {
  KEY: 'askai-storage-v10',
  
  // Load state from localStorage
  load: () => {
    try {
      const saved = localStorage.getItem(Storage.KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        console.log('📦 Loaded state from storage');
        return parsed;
      }
    } catch (e) {
      console.error('Error loading from storage:', e);
    }
    return null;
  },
  
  // Save state to localStorage
  save: (state) => {
    try {
      const toSave = {
        currentUser: state.currentUser,
        isAuthenticated: state.isAuthenticated,
        chats: state.chats,
        currentChatId: state.currentChatId,
        theme: state.theme,
      };
      localStorage.setItem(Storage.KEY, JSON.stringify(toSave));
    } catch (e) {
      console.error('Error saving to storage:', e);
    }
  },
  
  // Clear storage
  clear: () => {
    try {
      localStorage.removeItem(Storage.KEY);
      console.log('🗑️ Storage cleared');
    } catch (e) {
      console.error('Error clearing storage:', e);
    }
  },
  
  // Get specific key
  get: (key) => {
    try {
      const state = Storage.load();
      return state ? state[key] : null;
    } catch (e) {
      return null;
    }
  },
  
  // Set specific key
  set: (key, value) => {
    try {
      const state = Storage.load() || {};
      state[key] = value;
      Storage.save(state);
    } catch (e) {
      console.error('Error setting storage key:', e);
    }
  },
};
