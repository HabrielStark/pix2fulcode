import { useState, useRef } from 'react';
import { motion } from 'framer-motion';

interface UploadCardProps {
  onProcessingComplete?: (imageUrl?: string) => void;
}

export default function UploadCard({ onProcessingComplete }: UploadCardProps = {}) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      
      // Create a preview URL for the image
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
      
      // Reset progress
      setProgress(0);
    }
  };
  
  const handleUpload = async () => {
    if (!file || !previewUrl) return;
    
    setUploading(true);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 15;
        if (newProgress >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setUploading(false);
            // Notify parent component that processing is complete
            if (onProcessingComplete) {
              onProcessingComplete(previewUrl);
            } else {
              // Show alert if no callback provided
              alert('Upload complete! Processing your image...');
            }
          }, 500);
          return 100;
        }
        return newProgress;
      });
    }, 400);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files?.[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      
      // Create a preview URL for the image
      const url = URL.createObjectURL(droppedFile);
      setPreviewUrl(url);
      
      setProgress(0);
    }
  };

  const handleBrowse = () => {
    fileInputRef.current?.click();
  };
  
  return (
    <motion.div 
      className="retro-container p-8 m-4 max-w-md"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1 className="retro-title text-center mb-6 text-2xl">PIX2FULLCODE-3D</h1>
      
      <motion.div 
        className="border-2 border-dashed border-[var(--primary)] p-8 mb-6 text-center cursor-pointer"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleBrowse}
      >
        <input 
          type="file" 
          ref={fileInputRef}
          className="hidden" 
          accept="image/png, image/jpeg" 
          onChange={handleChange} 
        />
        
        {previewUrl ? (
          <div className="relative mb-4">
            <img 
              src={previewUrl} 
              alt="Preview" 
              className="max-h-40 mx-auto border-2 border-[var(--secondary)]" 
            />
          </div>
        ) : (
          <motion.div 
            className="mt-4 mb-2"
            animate={{ 
              scale: [1, 1.05, 1],
              borderColor: ['#ff6b6b', '#4ecdc4', '#ff6b6b']
            }}
            transition={{ duration: 3, repeat: Infinity }}
          >
            <svg className="w-12 h-12 mx-auto text-[var(--accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </motion.div>
        )}
        
        <p className="retro-text text-sm mb-2">
          {file ? file.name : "DRAG & DROP UI SCREENSHOT"}
        </p>
        <p className="text-[var(--secondary)] text-xs mt-1">OR CLICK TO BROWSE</p>
      </motion.div>
      
      {file && (
        <>
          <div className="retro-progress mb-4">
            <motion.div 
              className="retro-progress-bar"
              initial={{ width: '0%' }}
              animate={{ width: `${progress}%` }}
              transition={{ type: 'spring', damping: 10 }}
            />
          </div>
          
          <div className="flex space-x-4">
            <motion.button
              className="retro-button flex-1"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setFile(null);
                setProgress(0);
                if (previewUrl) {
                  URL.revokeObjectURL(previewUrl);
                  setPreviewUrl(null);
                }
              }}
              disabled={uploading}
            >
              RESET
            </motion.button>
            
            <motion.button
              className="retro-button flex-1"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleUpload}
              disabled={uploading}
              animate={
                uploading 
                  ? { 
                      backgroundColor: ['#ff6b6b', '#4ecdc4', '#ff6b6b'],
                      transition: { duration:
                      2, repeat: Infinity } 
                    } 
                  : {}
              }
            >
              {uploading ? "PROCESSING..." : "GENERATE CODE"}
            </motion.button>
          </div>
        </>
      )}
      
      <div className="text-[var(--accent)] text-xs mt-6 text-center">
        <motion.p
          animate={{ 
            opacity: [0.5, 1, 0.5],
          }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          UPLOAD UI SCREENSHOT → GET FULL 3D APP
        </motion.p>
    </div>
    </motion.div>
  );
}
