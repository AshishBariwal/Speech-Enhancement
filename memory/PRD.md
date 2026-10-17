# Speech Enhancement Web App - PRD

## Original Problem Statement
Build a website that uses a speech enhancement model. Users can upload WAV files or record noisy voice. Click predict to get filtered/enhanced voice. Show SNR and SI-SDR values. Play enhanced audio and download it.

## Architecture
- **Frontend**: React + Tailwind CSS + Framer Motion + Shadcn/UI
- **Backend**: FastAPI + MongoDB + SciPy
- **Storage**: Local file system for audio files, MongoDB for metadata

## User Personas
- Audio engineers testing speech enhancement models
- Researchers evaluating noise reduction algorithms
- General users wanting to clean up noisy recordings

## Core Requirements (Static)
1. Upload WAV files or record audio via microphone
2. Run speech enhancement prediction
3. Display SNR and SI-SDR metrics
4. Play original and enhanced audio with custom player
5. Download enhanced audio
6. Dark/light mode toggle
7. Apple-style glassmorphism UI with star effects

## What's Been Implemented (Feb 2026)
- Full-stack app with React frontend + FastAPI backend
- WAV file upload endpoint with MongoDB metadata storage
- Mock predict function (bandpass filter) - ready for real model integration
- Custom audio player with waveform visualization
- SNR and SI-SDR computation and display
- Audio recording via browser microphone (WebM to WAV conversion)
- Download enhanced audio
- Dark/light theme toggle with glassmorphic navbar
- Stars particle background animation
- Spring-based Framer Motion animations (Apple-style)
- Fonts: Outfit (headings), JetBrains Mono (metrics), Manrope (body)

## Prioritized Backlog
### P0 (Critical)
- [x] Upload WAV files
- [x] Predict/enhance audio
- [x] Show SNR & SI-SDR
- [x] Play enhanced audio
- [x] Download enhanced audio

### P1 (Important)
- [ ] Integrate real ML model (replace mock predict function)
- [ ] Waveform display for uploaded audio (static waveform)

### P2 (Nice to have)
- [ ] Batch processing multiple files
- [ ] History of past predictions
- [ ] Comparison view (side-by-side original vs enhanced waveforms)
- [ ] Real-time processing progress indicator

## Next Tasks
1. Replace mock `predict()` function with real ML model
2. Add static waveform visualization for uploaded audio
3. Add processing history with MongoDB storage
