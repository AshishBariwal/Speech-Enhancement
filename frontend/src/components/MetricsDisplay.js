import { motion } from 'framer-motion';
import { Activity, BarChart3 } from 'lucide-react';

function MetricCard({ label, value, unit, icon: Icon, delay }) {
  return (
    <motion.div
      data-testid={`metric-${label.toLowerCase().replace(/[\s-]+/g, '-')}`}
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25, delay }}
      whileHover={{ scale: 1.03, y: -2 }}
      className="relative overflow-hidden rounded-2xl p-6 border
        dark:bg-white/[0.03] dark:border-white/[0.06]
        bg-black/[0.02] border-black/[0.06]"
    >
      {/* Subtle gradient accent */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#FF5E00] to-[#E0004D] opacity-60" />

      <div className="flex items-start justify-between mb-4">
        <span className="text-[10px] font-jetbrains uppercase tracking-[0.2em] font-bold dark:text-zinc-500 text-zinc-400">
          {label}
        </span>
        <Icon className="w-4 h-4 dark:text-zinc-600 text-zinc-300" />
      </div>

      <div className="flex items-baseline gap-1.5">
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.2 }}
          className="text-4xl lg:text-5xl font-jetbrains font-light tracking-tight dark:text-white text-gray-900"
        >
          {value !== null ? value.toFixed(2) : '--'}
        </motion.span>
        <span className="text-sm font-jetbrains dark:text-zinc-500 text-zinc-400">{unit}</span>
      </div>
    </motion.div>
  );
}

export default function MetricsDisplay({ snr, siSdr }) {
  return (
    <div className="grid grid-cols-2 gap-4" data-testid="metrics-display">
      <MetricCard
        label="SNR"
        value={snr}
        unit="dB"
        icon={Activity}
        delay={0.1}
      />
      <MetricCard
        label="SI-SDR"
        value={siSdr}
        unit="dB"
        icon={BarChart3}
        delay={0.2}
      />
    </div>
  );
}
