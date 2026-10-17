import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, AudioLines, Mic, Upload as UploadIcon } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import axios from 'axios';

import FileUpload from './FileUpload';
import AudioRecorder from './AudioRecorder';
import PredictButton from './PredictButton';
import AudioPlayer from './AudioPlayer';
import MetricsDisplay from './MetricsDisplay';

const API = "http://localhost:8000/api";

export default function HomePage() {
  const [audioFile, setAudioFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [result, setResult] = useState(null);
  const [inputMode, setInputMode] = useState('upload');
  const [errorMsg, setErrorMsg] = useState(null);

  const originalAudioUrl = fileId ? `${API}/audio/${fileId}/original` : null;
  const enhancedAudioUrl = result ? `${API}/audio/${result.file_id}/enhanced` : null;

  const uploadFile = useCallback(async (file) => {
    setErrorMsg(null);
    if (!file) {
      setAudioFile(null);
      setFileId(null);
      setResult(null);
      return;
    }

    setAudioFile(file);
    setResult(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await axios.post(`${API}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setFileId(res.data.file_id);
    } catch (err) {
      console.error('Upload failed:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to upload audio file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  }, []);

  const handlePredict = async () => {
    if (!fileId) return;
    setErrorMsg(null);
    setIsPredicting(true);
    try {
      const res = await axios.post(`${API}/predict/${fileId}`);
      setResult(res.data);
    } catch (err) {
      console.error('Predict failed:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to enhance audio. Please check backend server.');
    } finally {
      setIsPredicting(false);
    }
  };
  const handleDownload = () => {
    if (!result) return;
    const link = document.createElement('a');
    link.href = `${API}/download/${result.file_id}`;
    link.download = `enhanced_${audioFile?.name || 'audio.wav'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleRecordingComplete = (file) => {
    uploadFile(file);
  };
  

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 relative z-10">
      <div className="max-w-3xl mx-auto">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20, delay: 0.1 }}
            className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[#FF5E00] to-[#E0004D] flex items-center justify-center shadow-lg shadow-[#FF5E00]/20"
          >
            <AudioLines className="w-8 h-8 text-white" />
          </motion.div>
          <h1 className="font-outfit text-4xl sm:text-5xl lg:text-6xl font-medium tracking-tighter dark:text-white text-gray-900 mb-3">
            Speech Enhancement
          </h1>
          <p className="font-manrope text-base dark:text-zinc-400 text-zinc-500 max-w-md mx-auto leading-relaxed">
            Upload or record noisy audio. Our model removes noise and enhances clarity instantly.
          </p>
        </motion.div>

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, type: 'spring', stiffness: 200, damping: 25 }}
          className="rounded-3xl p-6 sm:p-8 border backdrop-blur-sm mb-6
            dark:bg-white/[0.02] dark:border-white/[0.06]
            bg-white/60 border-black/[0.06] shadow-xl dark:shadow-none"
        >
          <Tabs value={inputMode} onValueChange={setInputMode} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6 dark:bg-white/[0.04] bg-black/[0.03] rounded-xl p-1 h-auto" data-testid="input-mode-tabs">
              <TabsTrigger
                value="upload"
                data-testid="tab-upload"
                className="rounded-lg py-2.5 text-sm font-manrope font-medium flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-[#FF5E00] data-[state=active]:to-[#E0004D] data-[state=active]:text-white data-[state=active]:shadow-md transition-all"
              >
                <UploadIcon className="w-4 h-4" />
                Upload
              </TabsTrigger>
              <TabsTrigger
                value="record"
                data-testid="tab-record"
                className="rounded-lg py-2.5 text-sm font-manrope font-medium flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-[#FF5E00] data-[state=active]:to-[#E0004D] data-[state=active]:text-white data-[state=active]:shadow-md transition-all"
              >
                <Mic className="w-4 h-4" />
                Record
              </TabsTrigger>
            </TabsList>

            <TabsContent value="upload">
              <FileUpload onFileSelect={uploadFile} disabled={isUploading || isPredicting} />
            </TabsContent>

            <TabsContent value="record">
              <AudioRecorder onRecordingComplete={handleRecordingComplete} disabled={isUploading || isPredicting} />
            </TabsContent>
          </Tabs>

          {/* Original Audio Player */}
          <AnimatePresence>
            {originalAudioUrl && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6"
              >
                <AudioPlayer audioUrl={originalAudioUrl} label="Original Audio" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error Banner */}
          <AnimatePresence>
            {errorMsg && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-manrope text-center"
              >
                {errorMsg}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Predict Button */}
          <div className="mt-6">
            <PredictButton
              onClick={handlePredict}
              isLoading={isPredicting}
              disabled={!fileId || isUploading}
            />
          </div>
        </motion.div>

        {/* Results Section */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              transition={{ type: 'spring', stiffness: 200, damping: 25 }}
              className="space-y-6"
            >
              {/* Metrics */}
              <MetricsDisplay snr={result.snr} siSdr={result.si_sdr} />

              {/* Enhanced Audio Player */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="rounded-3xl p-6 sm:p-8 border backdrop-blur-sm
                  dark:bg-white/[0.02] dark:border-white/[0.06]
                  bg-white/60 border-black/[0.06] shadow-xl dark:shadow-none"
              >
                <AudioPlayer audioUrl={enhancedAudioUrl} label="Enhanced Audio" accentColor="#10B981" />

                {/* Download Button */}
                <motion.button
                  data-testid="download-button"
                  onClick={handleDownload}
                  whileHover={{ scale: 1.02, y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                  className="mt-5 w-full py-3.5 rounded-xl font-manrope font-medium text-sm flex items-center justify-center gap-2.5
                    dark:bg-white/[0.06] dark:hover:bg-white/[0.1] dark:text-white
                    bg-black/[0.04] hover:bg-black/[0.08] text-gray-900
                    border dark:border-white/[0.06] border-black/[0.06]
                    transition-all duration-300"
                >
                  <Download className="w-4 h-4" />
                  Download Enhanced Audio
                </motion.button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
