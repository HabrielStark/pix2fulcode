import React from 'react';
import { motion } from 'framer-motion';

interface ViewerProps {
  data: {
    status: string;
    reason?: string;
    download?: string;
    imageUrl?: string;
    fallback?: boolean;
    glb_url?: string | null;
  };
  retry3D: () => void;
  backToUpload?: () => void;
}

const Viewer3D: React.FC<ViewerProps> = ({ data, retry3D, backToUpload }) => {
  // Проверка на фейковый результат - когда fallback=true и нет glb_url
  if (data.fallback && !data.glb_url) {
    return (
      <motion.div 
        className="retro-container mx-auto max-w-lg p-6 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <motion.div
          animate={{ 
            borderColor: ['#ff6b6b', '#ff0000', '#ff6b6b'],
            boxShadow: [
              '0 0 0 4px var(--background), 0 0 0 6px var(--primary)', 
              '0 0 20px 4px #ff0000, 0 0 0 6px #ff0000', 
              '0 0 0 4px var(--background), 0 0 0 6px var(--primary)'
            ]
          }}
          transition={{ duration: 2, repeat: Infinity }}
          className="border-4 border-[var(--primary)] p-4 mb-4"
        >
          <h2 className="retro-title mb-2 text-xl">NO 3D MESH PRODUCED</h2>
          <motion.svg 
            className="w-16 h-16 mx-auto text-[var(--primary)] my-4"
            viewBox="0 0 24 24"
            animate={{ 
              rotate: [0, 5, -5, 0],
              scale: [1, 1.1, 1]
            }}
            transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
          >
            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
          </motion.svg>
          <p className="text-[var(--text)] mb-4">
            {data.reason || "❌ 3D Generation Failed. No mesh was produced. Please try another image or adjust prompt."}
          </p>
        </motion.div>
        
        <div className="flex space-x-4">
          {backToUpload && (
            <motion.button 
              onClick={backToUpload}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="retro-button flex-1"
            >
              TRY ANOTHER IMAGE
            </motion.button>
          )}
        </div>
      </motion.div>
    );
  }

  // Error state - when 3D generation failed
  if (data.status === 'FAILED') {
    return (
      <motion.div 
        className="retro-container mx-auto max-w-lg p-6 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <motion.div
          animate={{ 
            borderColor: ['#ff6b6b', '#ff0000', '#ff6b6b'],
            boxShadow: [
              '0 0 0 4px var(--background), 0 0 0 6px var(--primary)', 
              '0 0 20px 4px #ff0000, 0 0 0 6px #ff0000', 
              '0 0 0 4px var(--background), 0 0 0 6px var(--primary)'
            ]
          }}
          transition={{ duration: 2, repeat: Infinity }}
          className="border-4 border-[var(--primary)] p-4 mb-4"
        >
          <h2 className="retro-title mb-2 text-xl">3D GENERATION FAILED</h2>
          <motion.svg 
            className="w-16 h-16 mx-auto text-[var(--primary)] my-4"
            viewBox="0 0 24 24"
            animate={{ 
              rotate: [0, 5, -5, 0],
              scale: [1, 1.1, 1]
            }}
            transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
          >
            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
          </motion.svg>
          <p className="text-[var(--text)] mb-4">{data.reason}</p>
        </motion.div>
        
        <div className="flex space-x-4">
          <motion.button 
            onClick={retry3D}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="retro-button flex-1"
          >
            RETRY IN 2-D MODE
          </motion.button>
          
          {backToUpload && (
            <motion.button 
              onClick={backToUpload}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="retro-button flex-1"
            >
              NEW IMAGE
            </motion.button>
          )}
        </div>
      </motion.div>
    );
  }

  // Success state - when 3D model is available (убедимся, что это не fallback результат)
  if (data.status === 'SUCCESS' && data.download && !data.fallback) {
    return (
      <motion.div 
        className="retro-container mx-auto max-w-lg p-6 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h2 className="retro-title mb-6 text-xl">3D GENERATION COMPLETE!</h2>
        
        <div className="retro-container p-4 mb-6 h-64 flex items-center justify-center">
          {data.imageUrl ? (
            <motion.div 
              className="w-32 h-64 relative perspective-500"
              animate={{ 
                rotateY: [0, 360],
                rotateX: [0, 15, 0, -15, 0]
              }}
              transition={{ duration: 10, repeat: Infinity, repeatType: 'loop' }}
              style={{ 
                transformStyle: 'preserve-3d',
                perspective: '1000px'
              }}
            >
              <img 
                src={data.imageUrl} 
                alt="3D Model" 
                className="w-full h-full object-contain"
                style={{
                  transform: 'translateZ(20px)',
                  boxShadow: '0 0 15px rgba(78, 205, 196, 0.8)'
                }}
              />
            </motion.div>
          ) : (
            <motion.div
              animate={{ 
                rotateY: [0, 360],
                rotateX: [0, 45, 0, -45, 0]
              }}
              transition={{ duration: 10, repeat: Infinity, repeatType: 'loop' }}
              className="w-32 h-32 relative"
            >
              <div className="absolute inset-0 bg-[var(--primary)] transform rotate-45"></div>
              <div className="absolute inset-0 bg-[var(--secondary)] transform rotate-[135deg]"></div>
            </motion.div>
          )}
        </div>
        
        <div className="flex space-x-4">
          <motion.a 
            href={data.download}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="retro-button flex-1"
            download
          >
            DOWNLOAD FILES
          </motion.a>
          
          {backToUpload ? (
            <motion.button 
              onClick={backToUpload}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="retro-button flex-1"
            >
              NEW PROJECT
            </motion.button>
          ) : (
            <motion.button 
              onClick={() => window.location.reload()}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="retro-button flex-1"
            >
              RESTART
            </motion.button>
          )}
        </div>
      </motion.div>
    );
  }

  // Loading state or other states
  return (
    <motion.div 
      className="retro-container mx-auto max-w-lg p-6 text-center"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h2 className="retro-title mb-6 text-xl">GENERATING 3D MODEL</h2>
      
      <div className="flex flex-col items-center justify-center h-64">
        {data.imageUrl ? (
          <div className="relative mb-6">
            <img 
              src={data.imageUrl} 
              alt="Processing" 
              className="max-h-32 mx-auto border-2 border-[var(--secondary)] opacity-50" 
            />
            <motion.div 
              className="absolute inset-0 border-2 border-[var(--primary)]"
              animate={{ 
                opacity: [0, 1, 0],
                scale: [0.8, 1.1, 0.8],
              }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>
        ) : (
          <motion.div
            animate={{ 
              rotate: [0, 360],
              borderRadius: ["20%", "20%", "50%", "50%", "20%"]
            }}
            transition={{ duration: 3, repeat: Infinity }}
            className="w-16 h-16 mb-8 border-4 border-t-[var(--primary)] border-r-[var(--secondary)] border-b-[var(--accent)] border-l-[var(--primary)]"
          ></motion.div>
        )}
        
        <motion.p
          className="retro-text text-sm"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          BUILDING YOUR CREATION...
        </motion.p>
      </div>
    </motion.div>
  );
};

export default Viewer3D; 