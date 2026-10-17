# 🎙️ DeepFilterNet Speech Enhancement UI

> An end-to-end, AI-powered web application that removes background noise from speech and audio recordings using PyTorch DeepFilterLite neural model.

---

## 🌟 Key Features

- 🎧 **AI Speech Enhancement**: Removes background noise, hums, traffic, and static using PyTorch DeepFilterLite (`best.pt`).
- 📁 **Universal Audio Support**: Upload any audio file: `.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`, `.aac`, `.wma`.
- 🎙️ **Live Microphone Recording**: Record noisy speech directly from your browser microphone and clean it up instantly.
- 📊 **Dual Waveform Visualization**: Interactive audio player powered by `WaveSurfer.js` to visually compare raw vs. cleaned audio side-by-side.
- 📈 **Real-Time Quality Metrics**: Calculates Signal-to-Noise Ratio (**SNR**) improvement and **SI-SDR** scores.
- 💾 **One-Click Download**: Export clean, enhanced high-quality audio files with a single click.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.9+, FastAPI, PyTorch, Torchaudio, SoundFile, Motor (MongoDB Async Driver), Uvicorn.
- **Frontend**: React 19, Tailwind CSS, Framer Motion, WaveSurfer.js, Lucide Icons, Radix UI.
- **Database**: MongoDB (stores file metadata and processing history).

---

## 🔰 Novice-Friendly Setup & Requirements Guide

If you are new to programming or running local projects, follow these 3 easy installation steps first:

### 1. Install Node.js (for Frontend UI)
- Download Node.js **LTS version** from [nodejs.org](https://nodejs.org/).
- Run the installer and click **Next** through all steps.

### 2. Install Python (for AI Backend Model)
- Download Python **3.10 or 3.11** from [python.org](https://www.python.org/downloads/).
- ⚠️ **IMPORTANT**: During installation on Windows, check the box that says **"Add Python to PATH"** before clicking Install.

### 3. Database Option (MongoDB)
Choose **one** of the following options:
- **Option A (Local)**: Download & Install [MongoDB Community Server](https://www.mongodb.com/try/download/community).
- **Option B (Cloud - No Install)**: Create a free database at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and set your connection URL in `backend/.env`.

---

## 🚀 How to Run the Application

### Method 1: ⚡ 1-Click Launch (Windows - Easiest)

1. Double-click the **`start.bat`** file located in the root folder of this project.
2. It will automatically launch two terminal windows:
   - **Backend Server**: running on `http://localhost:8000`
   - **Frontend UI**: running on `http://localhost:3000`
3. Open your browser and go to: 👉 **[http://localhost:3000](http://localhost:3000)**

---

### Method 2: 🛠️ Step-by-Step Manual Launch (Windows / Mac / Linux)

#### **Step 1: Start the Backend (FastAPI & PyTorch Model)**

Open a terminal window and run:

```bash
# 1. Navigate into the backend directory
cd backend

# 2. (Optional) Create and activate a Python virtual environment
python -m venv venv

# On Windows PowerShell:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install required Python packages
pip install -r requirements.txt

# 4. Start the FastAPI server
python -m uvicorn server:app --reload --port 8000
```

#### **Step 2: Start the Frontend (React Web App)**

Open a **second terminal window** and run:

```bash
# 1. Navigate into the frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the React development server
npm start
```

Your browser will automatically open **`http://localhost:3000`**!

---

## 🎧 How to Use the Application

1. **Choose Input Method**:
   - **Upload Tab**: Drag and drop your `.mp3` or `.wav` noisy audio file.
   - **Record Tab**: Click the microphone icon to record your voice live.
2. **Listen to Original Audio**: Use the top interactive waveform player to preview your input recording.
3. **Enhance Speech**: Click the **Enhance Audio** button.
4. **Compare & Download**: View the calculated **SNR improvements**, play the cleaned audio on the bottom waveform player, and click **Download Enhanced Audio**!

---

## 📂 Project Structure

```text
DeepFilterNetUI-speachEnhancement/
├── backend/
│   ├── best.pt           # Pre-trained PyTorch DeepFilterLite weights
│   ├── model.py          # Pure PyTorch DeepFilterLite architecture
│   ├── server.py         # FastAPI REST API endpoints
│   ├── spectrum.py       # Audio STFT & spectrogram utilities
│   ├── requirements.txt  # Python backend dependencies
│   └── .env              # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── components/   # React UI components (AudioPlayer, FileUpload, etc.)
│   │   ├── App.js        # Main application component
│   │   └── index.js      # Entry point
│   ├── package.json      # Frontend package dependencies
│   └── tailwind.config.js# Tailwind CSS styling configuration
├── start.bat             # 1-Click launcher script for Windows
└── README.md             # Project documentation & instructions
```

---

## ❓ Common Questions & Troubleshooting (FAQ)

<details>
<summary><b>Q: What does error code 100 mean when starting MongoDB?</b></summary>
<b>A:</b> Exit code 100 means MongoDB is <b>already running</b> in the background on your machine. You can proceed directly to starting the application!
</details>

<details>
<summary><b>Q: `python` or `npm` command is not recognized in terminal?</b></summary>
<b>A:</b> Make sure Python and Node.js are installed and added to your system environment variables (PATH). Restart your terminal after installing.
</details>

<details>
<summary><b>Q: Can I upload non-WAV files like MP3 or M4A?</b></summary>
<b>A:</b> Yes! The application automatically converts MP3, FLAC, OGG, M4A, and AAC files to normalized WAV format upon upload.
</details>

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/` | Health check & device info (CPU/CUDA) |
| `POST` | `/api/upload` | Upload audio file (`.mp3`, `.wav`, etc.) |
| `POST` | `/api/predict/{file_id}` | Process & enhance uploaded audio |
| `GET` | `/api/audio/{file_id}/{audio_type}` | Retrieve `original` or `enhanced` audio file |
| `GET` | `/api/download/{file_id}` | Download cleaned WAV file |

---

## 📄 License

This project is open-source and built for speech processing and deep learning audio enhancement applications.
