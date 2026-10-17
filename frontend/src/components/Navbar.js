import { motion } from 'framer-motion';
import { Sun, Moon, AudioLines } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

export default function Navbar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.nav
      data-testid="navbar"
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30, delay: 0.1 }}
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-2xl border-b
        dark:bg-black/60 dark:border-white/[0.08]
        bg-white/70 border-black/[0.05]"
    >
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <motion.div
          className="flex items-center gap-3"
          whileHover={{ scale: 1.02 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#FF5E00] to-[#E0004D] flex items-center justify-center">
            <AudioLines className="w-5 h-5 text-white" />
          </div>
          <span className="font-outfit text-lg font-medium tracking-tight dark:text-white text-gray-900">
            SpeechCraft
          </span>
        </motion.div>

        <motion.button
          data-testid="theme-toggle"
          onClick={toggleTheme}
          whileHover={{ scale: 1.1, rotate: 15 }}
          whileTap={{ scale: 0.9 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          className="w-10 h-10 rounded-full flex items-center justify-center
            dark:bg-white/[0.06] dark:hover:bg-white/[0.12]
            bg-black/[0.04] hover:bg-black/[0.08]
            transition-colors duration-300"
        >
          {theme === 'dark' ? (
            <Sun className="w-[18px] h-[18px] text-amber-400" />
          ) : (
            <Moon className="w-[18px] h-[18px] text-slate-700" />
          )}
        </motion.button>
      </div>
    </motion.nav>
  );
}
