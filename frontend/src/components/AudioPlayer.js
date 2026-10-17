import { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Volume2, VolumeX } from 'lucide-react';
import { Slider } from '../components/ui/slider';

export default function AudioPlayer({ audioUrl, label, accentColor = '#FF5E00' }) {
  const audioRef = useRef(null);
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const analyserRef = useRef(null);
  const audioCtxRef = useRef(null);
  const sourceRef = useRef(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);

  const setupAnalyser = useCallback(() => {
    if (!audioRef.current) return;

    // Create AudioContext once
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }

    // Create analyser once
    if (!analyserRef.current) {
      analyserRef.current = audioCtxRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
    }

    // 🔥 FIX: create source ONLY ONCE
    if (!sourceRef.current) {
      sourceRef.current =
        audioCtxRef.current.createMediaElementSource(audioRef.current);

      sourceRef.current.connect(analyserRef.current);
      analyserRef.current.connect(audioCtxRef.current.destination);
    }
  }, []);

  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.85;
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - barHeight);
        gradient.addColorStop(0, accentColor);
        gradient.addColorStop(1, '#E0004D');

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, canvas.height - barHeight, barWidth - 1.5, barHeight, 2);
        ctx.fill();

        x += barWidth;
      }
    };
    draw();
  }, [accentColor]);

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

useEffect(() => {
  // Reset player state
  setIsPlaying(false);
  setCurrentTime(0);
  setDuration(0);

  if (animFrameRef.current) {
    cancelAnimationFrame(animFrameRef.current);
  }

  // Close audio context safely
  if (audioCtxRef.current) {
    audioCtxRef.current.close();
  }

  // 🔥 ALWAYS reset refs (outside if)
  audioCtxRef.current = null;
  analyserRef.current = null;
  sourceRef.current = null;

}, [audioUrl]);

  const togglePlay = async () => {
    if (!audioRef.current) return;
    setupAnalyser();

    if (audioCtxRef.current?.state === 'suspended') {
      await audioCtxRef.current.resume();
    }

    if (isPlaying) {
      audioRef.current.pause();
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    } else {
      await audioRef.current.play();
      drawWaveform();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) setCurrentTime(audioRef.current.currentTime);
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) setDuration(audioRef.current.duration);
  };

  const handleEnded = () => {
    setIsPlaying(false);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
  };

  const handleSeek = (value) => {
    if (audioRef.current) {
      audioRef.current.currentTime = value[0];
      setCurrentTime(value[0]);
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const formatTime = (t) => {
    if (!t || isNaN(t)) return '0:00';
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (!audioUrl) return null;

  return (
    <motion.div
      data-testid={`audio-player-${label?.toLowerCase().replace(/\s+/g, '-') || 'default'}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className="rounded-2xl p-5 dark:bg-white/[0.03] bg-black/[0.02] border dark:border-white/[0.06] border-black/[0.06]"
    >
  <audio
    key={audioUrl}   // 🔥 THIS FIXES EVERYTHING
    ref={audioRef}
    src={audioUrl}
    onTimeUpdate={handleTimeUpdate}
    onLoadedMetadata={handleLoadedMetadata}
    onEnded={handleEnded}
    crossOrigin="anonymous"
  />

      {label && (
        <p className="text-xs font-manrope uppercase tracking-[0.15em] dark:text-zinc-500 text-zinc-400 mb-3 font-bold">
          {label}
        </p>
      )}

      {/* Waveform visualizer */}
      <div className="w-full h-16 mb-4 rounded-xl overflow-hidden dark:bg-white/[0.02] bg-black/[0.02]">
        <canvas
          ref={canvasRef}
          width={600}
          height={64}
          className="w-full h-full"
        />
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        <motion.button
          data-testid={`play-btn-${label?.toLowerCase().replace(/\s+/g, '-') || 'default'}`}
          onClick={togglePlay}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          className="w-10 h-10 rounded-full flex items-center justify-center
            bg-gradient-to-br from-[#FF5E00] to-[#E0004D] shadow-lg shadow-[#FF5E00]/20"
        >
          {isPlaying ? (
            <Pause className="w-4 h-4 text-white fill-white" />
          ) : (
            <Play className="w-4 h-4 text-white fill-white ml-0.5" />
          )}
        </motion.button>

        <div className="flex-1 flex flex-col gap-1">
          <Slider
            data-testid={`seek-slider-${label?.toLowerCase().replace(/\s+/g, '-') || 'default'}`}
            value={[currentTime]}
            max={duration || 100}
            step={0.1}
            onValueChange={handleSeek}
            className="cursor-pointer"
          />
          <div className="flex justify-between">
            <span className="text-[10px] font-jetbrains dark:text-zinc-500 text-zinc-400 tabular-nums">
              {formatTime(currentTime)}
            </span>
            <span className="text-[10px] font-jetbrains dark:text-zinc-500 text-zinc-400 tabular-nums">
              {formatTime(duration)}
            </span>
          </div>
        </div>

        <motion.button
          data-testid={`mute-btn-${label?.toLowerCase().replace(/\s+/g, '-') || 'default'}`}
          onClick={toggleMute}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="dark:text-zinc-400 text-zinc-500 dark:hover:text-white hover:text-black transition-colors"
        >
          {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </motion.button>
      </div>
    </motion.div>
  );
}
