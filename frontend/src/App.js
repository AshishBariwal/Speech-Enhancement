import "@/App.css";
import { ThemeProvider } from "./contexts/ThemeContext";
import Navbar from "./components/Navbar";
import StarsBackground from "./components/StarsBackground";
import HomePage from "./components/HomePage";

function App() {
  return (
    <ThemeProvider>
      <div className="App relative min-h-screen dark:bg-[#050505] bg-[#FAFAFA] transition-colors duration-500">
        <StarsBackground />
        <Navbar />
        <HomePage />
      </div>
    </ThemeProvider>
  );
}

export default App;
