import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileAudio, X, CheckCircle2 } from 'lucide-react';

export default function FileUpload({ onFileSelect, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const inputRef = useRef(null);

  const ALLOWED_EXTENSIONS = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma'];

  const handleFile = useCallback((file) => {
    if (file) {
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (ALLOWED_EXTENSIONS.includes(ext)) {
        setSelectedFile(file);
        onFileSelect(file);
      }
    }
  }, [onFileSelect]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }, [handleFile]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const clearFile = () => {
    setSelectedFile(null);
    onFileSelect(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <motion.div
      data-testid="upload-dropzone"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25, delay: 0.2 }}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300
        ${isDragging
          ? 'border-[#FF5E00] dark:bg-[#FF5E00]/[0.06] bg-[#FF5E00]/[0.04] scale-[1.02]'
          : selectedFile
            ? 'border-emerald-500/40 dark:bg-emerald-500/[0.04] bg-emerald-50'
            : 'dark:border-white/[0.1] border-black/[0.1] dark:hover:border-white/[0.2] hover:border-black/[0.2] dark:bg-white/[0.02] bg-black/[0.01]'
        }
        ${disabled ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept="audio/*,.wav,.mp3,.ogg,.flac,.m4a,.aac"
        className="hidden"
        data-testid="file-input"
        onChange={(e) => handleFile(e.target.files[0])}
      />

      <AnimatePresence mode="wait">
        {selectedFile ? (
          <motion.div
            key="selected"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex flex-col items-center gap-3"
          >
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
              <CheckCircle2 className="w-7 h-7 text-emerald-500" />
            </div>
            <div className="flex items-center gap-2">
              <FileAudio className="w-4 h-4 dark:text-zinc-400 text-zinc-500" />
              <span className="text-sm font-manrope dark:text-zinc-300 text-zinc-700 truncate max-w-[200px]">
                {selectedFile.name}
              </span>
              <button
                data-testid="clear-file-btn"
                onClick={(e) => { e.stopPropagation(); clearFile(); }}
                className="ml-1 p-1 rounded-full dark:hover:bg-white/10 hover:bg-black/10 transition-colors"
              >
                <X className="w-3.5 h-3.5 dark:text-zinc-400 text-zinc-500" />
              </button>
            </div>
            <span className="text-xs dark:text-zinc-500 text-zinc-400 font-manrope">
              {(selectedFile.size / 1024).toFixed(1)} KB
            </span>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-3"
          >
            <motion.div
              animate={isDragging ? { scale: 1.15, rotate: 5 } : { scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="w-14 h-14 rounded-2xl dark:bg-white/[0.04] bg-black/[0.03] flex items-center justify-center"
            >
              <Upload className="w-7 h-7 dark:text-zinc-400 text-zinc-500" />
            </motion.div>
            <div>
              <p className="text-sm font-manrope font-medium dark:text-zinc-300 text-zinc-700">
                Drop your audio file here (MP3, WAV, FLAC, OGG, M4A)
              </p>
              <p className="text-xs dark:text-zinc-500 text-zinc-400 mt-1 font-manrope">
                or click to browse
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
