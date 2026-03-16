/* =====================================================
   ASK AI - Custom React Hooks
   Authors: Annor Prince & Yeboah Collins
   ===================================================== */

// File handling hook
const useFileHandler = () => {
  const [selectedFiles, setSelectedFiles] = React.useState([]);
  const [processingFile, setProcessingFile] = React.useState(false);
  const { toast } = useToast();
  
  const processFiles = async (files) => {
    const processedFiles = [];
    
    for (const file of files) {
      // Check file size
      if (file.size > CONFIG.MAX_FILE_SIZE) {
        toast('File Too Large', `${file.name} exceeds 50MB limit`, 'error');
        continue;
      }
      
      // Check file type
      const category = Utils.getFileCategory(file.name);
      if (category === 'unknown') {
        toast('Unsupported Format', `${file.name} format not supported`, 'error');
        continue;
      }
      
      // Read file as base64
      try {
        const base64 = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
        
        processedFiles.push({
          name: file.name,
          type: file.type,
          size: file.size,
          category,
          data: base64,
        });
      } catch (e) {
        toast('Error', `Failed to read ${file.name}`, 'error');
      }
    }
    
    return processedFiles;
  };
  
  const handleFileSelect = async (fileList) => {
    const files = Array.from(fileList);
    const processed = await processFiles(files);
    setSelectedFiles(prev => [...prev, ...processed]);
    
    if (processed.length > 0) {
      toast('Files Added', `${processed.length} file(s) ready`, 'success');
    }
  };
  
  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };
  
  const clearFiles = () => {
    setSelectedFiles([]);
  };
  
  return {
    selectedFiles,
    processingFile,
    setProcessingFile,
    handleFileSelect,
    removeFile,
    clearFiles,
  };
};

// Voice recording hook
const useVoiceRecording = () => {
  const [isRecording, setIsRecording] = React.useState(false);
  const [recordingTime, setRecordingTime] = React.useState(0);
  const [audioBlob, setAudioBlob] = React.useState(null);
  const [audioUrl, setAudioUrl] = React.useState(null);
  const [mediaRecorder, setMediaRecorder] = React.useState(null);
  const [recordingTimer, setRecordingTimer] = React.useState(null);
  const { toast } = useToast();
  
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: CONFIG.VOICE_MIME_TYPE
      });
      
      const chunks = [];
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };
      
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: CONFIG.VOICE_MIME_TYPE });
        const url = URL.createObjectURL(blob);
        setAudioBlob(blob);
        setAudioUrl(url);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      const timer = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= CONFIG.MAX_VOICE_DURATION - 1) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
      setRecordingTimer(timer);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      toast('Microphone Error', 'Could not access microphone. Please check permissions.', 'error');
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    if (recordingTimer) {
      clearInterval(recordingTimer);
    }
    setIsRecording(false);
    setRecordingTimer(null);
  };
  
  const cancelRecording = () => {
    stopRecording();
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingTime(0);
  };
  
  const clearRecording = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingTime(0);
  };
  
  const getAudioBase64 = async () => {
    if (!audioBlob) return null;
    return Utils.audioBlobToBase64(audioBlob);
  };
  
  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (recordingTimer) {
        clearInterval(recordingTimer);
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, []);
  
  return {
    isRecording,
    recordingTime,
    audioBlob,
    audioUrl,
    startRecording,
    stopRecording,
    cancelRecording,
    clearRecording,
    getAudioBase64,
  };
};

// Speech recognition hook
const useSpeechRecognition = () => {
  const [isListening, setIsListening] = React.useState(false);
  const [transcript, setTranscript] = React.useState('');
  const recognitionRef = React.useRef(null);
  const { toast } = useToast();
  
  const startListening = () => {
    if (!Utils.supportsSpeechRecognition()) {
      toast('Not Supported', 'Speech recognition not supported in this browser', 'error');
      return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
      setIsListening(false);
    };
    
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      if (event.error !== 'aborted') {
        toast('Recognition Error', 'Could not recognize speech. Please try again.', 'error');
      }
    };
    
    recognition.onend = () => {
      setIsListening(false);
    };
    
    recognitionRef.current = recognition;
    window.speechRecognition = recognition;
    recognition.start();
    setIsListening(true);
  };
  
  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };
  
  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };
  
  return {
    isListening,
    transcript,
    setTranscript,
    startListening,
    stopListening,
    toggleListening,
  };
};
