import Head from 'next/head'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import UploadCard from '../components/UploadCard'
import Viewer3D from '../components/Viewer3D'

interface ResultData {
  status: string;
  reason?: string;
  download?: string;
  imageUrl?: string;
  fallback?: boolean;
  glb_url?: string | null;
}

interface StarProps {
  top: string;
  left: string;
  delay: number;
  duration: number;
}

export default function Home() {
  const [view, setView] = useState<'upload' | 'result'>('upload')
  const [resultData, setResultData] = useState<ResultData>({ status: 'LOADING' })
  const [stars, setStars] = useState<StarProps[]>([])
  const [isClient, setIsClient] = useState(false)

  // This simulates a handler for when a result is ready - with proper flags for real 3D success
  const handleRetry3D = () => {
    setResultData({ 
      status: 'SUCCESS', 
      download: '/sample.zip',
      imageUrl: resultData.imageUrl,
      glb_url: '/path/to/real.glb',
      fallback: false
    });
  }
  
  // Handler for when upload is complete
  const handleUploadComplete = (imageUrl?: string) => {
    // First set loading state
    setResultData({ 
      status: 'LOADING',
      imageUrl 
    });
    setView('result');
    
    // Simulate backend processing
    setTimeout(() => {
      // 20% chance of fallback without glb (для демонстрации проблемы, которую описал пользователь)
      if (Math.random() < 0.2) {
        setResultData({ 
          status: 'SUCCESS',  // Подмена - выглядит как успех, но это не так!
          download: '/fake-archive.zip',
          imageUrl,
          fallback: true,
          glb_url: null,
          reason: "NO_MESH: 3D generation failed, image returned instead."
        });
      }
      // 20% chance of regular failure
      else if (Math.random() < 0.4) {
        setResultData({ 
          status: 'FAILED', 
          reason: 'Could not determine UI elements from screenshot. Try a different image.',
          imageUrl 
        });
      } 
      // 60% chance of real success
      else {
        setResultData({ 
          status: 'SUCCESS', 
          download: '/sample.zip',
          imageUrl,
          glb_url: '/path/to/real.glb',
          fallback: false
        });
      }
    }, 3000);
  }
  
  // Reset to upload view
  const resetToUpload = () => {
    setView('upload');
  }

  // Generate stars only on client-side to avoid hydration mismatch
  useEffect(() => {
    setIsClient(true)
    
    const generatedStars = Array.from({ length: 50 }).map(() => ({
      top: `${Math.random() * 100}%`,
      left: `${Math.random() * 100}%`,
      delay: Math.random() * 5,
      duration: 1 + Math.random() * 3
    }))
    
    setStars(generatedStars)
  }, [])

  return (
    <>
      <Head>
        <title>Retro Pix2FullCode-3D</title>
      </Head>
      
      <div className="min-h-screen bg-[var(--background)] overflow-hidden relative">
        {/* Background grid effect */}
        <div className="absolute inset-0 z-0" style={{
          backgroundImage: `linear-gradient(var(--primary) 1px, transparent 1px), 
                            linear-gradient(90deg, var(--primary) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
          backgroundPosition: '-1px -1px',
          opacity: 0.1
        }} />
        
        {/* Retro stars - only render on client side */}
        {isClient && (
          <motion.div 
            className="absolute inset-0 z-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.3 }}
            transition={{ duration: 2 }}
          >
            {stars.map((star, i) => (
              <motion.div
                key={i}
                className="absolute w-1 h-1 bg-white rounded-full"
                style={{
                  top: star.top,
                  left: star.left,
                }}
                animate={{ 
                  opacity: [0.1, 1, 0.1],
                  scale: [1, 1.5, 1]
                }}
                transition={{ 
                  duration: star.duration,
                  repeat: Infinity,
                  delay: star.delay
                }}
              />
            ))}
          </motion.div>
        )}
        
        <main className="flex flex-col items-center justify-center min-h-screen py-10 px-4 relative z-10">
          <motion.div
            className="text-center mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <motion.h1 
              className="retro-title text-4xl mb-2"
              animate={{ 
                textShadow: [
                  '3px 3px 0 var(--primary)', 
                  '5px 5px 0 var(--primary)', 
                  '3px 3px 0 var(--primary)'
                ] 
              }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              PIX2FULLCODE-3D
            </motion.h1>
            <p className="text-[var(--text)]">Upload UI → Get Working 3D App</p>
          </motion.div>
          
          {view === 'upload' ? (
            <UploadCard onProcessingComplete={handleUploadComplete} />
          ) : (
            <Viewer3D 
              data={resultData} 
              retry3D={handleRetry3D}
              backToUpload={resetToUpload}
            />
          )}
          
          <motion.div 
            className="mt-10 text-[var(--text)] text-sm text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.7 }}
            transition={{ delay: 0.5 }}
          >
            <p>Made with retro love {new Date().getFullYear()}</p>
          </motion.div>
        </main>
      </div>
    </>
  )
}
