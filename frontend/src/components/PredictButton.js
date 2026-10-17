import { motion } from 'framer-motion';
import { Sparkles, Loader2 } from 'lucide-react';

export default function PredictButton({ onClick, isLoading, disabled }) {
  return (
    <motion.button
      data-testid="predict-button"
      onClick={onClick}
      disabled={disabled || isLoading}
      whileHover={!disabled && !isLoading ? { scale: 1.03, y: -1 } : {}}
      whileTap={!disabled && !isLoading ? { scale: 0.97 } : {}}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      className={`relative w-full py-4 px-8 rounded-2xl font-outfit font-medium text-base tracking-tight
        overflow-hidden transition-all duration-300 group
        ${disabled || isLoading
          ? 'opacity-40 cursor-not-allowed'
          : 'cursor-pointer'
        }`}
    >
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#FF5E00] to-[#E0004D] transition-opacity duration-300" />

      {/* Shimmer sweep on hover */}
      {!disabled && !isLoading && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          initial={{ x: '-100%' }}
          whileHover={{ x: '100%' }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
        />
      )}

      {/* Button content */}
      <div className="relative z-10 flex items-center justify-center gap-2.5 text-white">
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Enhancing Audio...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            <span>Enhance Audio</span>
          </>
        )}
      </div>

      {/* Glow effect */}
      {!disabled && !isLoading && (
        <div className="absolute -bottom-1 left-1/4 right-1/4 h-8 bg-gradient-to-r from-[#FF5E00] to-[#E0004D] blur-2xl opacity-40 group-hover:opacity-60 transition-opacity" />
      )}
    </motion.button>
  );
}
