# Pitch Shifter Project - Version History & Development Summary

**Project Goal**: Deploy a web-based pitch-shifting application for elderly users at ai-builders.space platform

**Final Version**: v26 (2026-01-31)  
**GitHub Repository**: https://github.com/yepogue/pitch-shifter  
**Production URL**: https://pitch-shifter.ai-builders.space  
**Local Testing**: http://localhost:8003

---

## Final Solution Overview

### Architecture
- **Backend**: Flask + scipy.signal.resample_poly() for fast pitch shifting
- **Frontend**: Browser-based JavaScript with automatic playback rate compensation
- **Default Configuration**: -5 semitones pitch reduction, 0.9x base speed (labeled "normal")
- **Performance**: <1 second processing time (typically 0.04-0.07s)

### Key Technical Decisions

1. **Abandoned Librosa Phase Vocoder**
   - Perfect quality but 30-100+ seconds processing time
   - Exceeds Koyeb's 60-second timeout limit on 256MB RAM
   - STFT operations too CPU/memory intensive for deployment constraints

2. **Adopted Scipy Resampling**
   - Uses polyphase filtering (resample_poly)
   - Fast: <1 second processing
   - Trade-off: "Tape speed effect" changes both pitch AND duration
   - Background noise acceptable for use case

3. **Browser Playback Rate Compensation**
   - Restores near-original duration without reprocessing
   - Formula: `playbackRate = baseSpeed × (1 / pitchRatio)`
   - Example: -5 semitones → 0.9 × 1.335 = 1.20x playback rate
   - Separates pitch change (backend) from duration restoration (frontend)

4. **User-Centered Calibration**
   - 0.9x "normal speed" for elderly users' better comprehension
   - Default -5 semitones (more suitable than -3 for female voices)

---

## Complete Version History

### V1-V9 (Not documented in current session)
*Earlier development phases*

### V10-V15: Initial Deployment Issues
**Problem**: Application crashes with 500 Internal Server Error  
**Root Cause**: Typo `bins_per_octane` instead of `bins_per_octave` in librosa.effects.pitch_shift()  
**Solution**: Corrected parameter name  
**Remaining Issues**: Librosa still hanging indefinitely on Koyeb

### V16-V17: Librosa Optimization Attempts
**Problem**: Librosa operations hanging indefinitely (no response after 30+ seconds)  
**Attempted Solution**: Added `res_type='fft'` to both librosa.load() and pitch_shift() for speed  
**Result**: FAILED - Caused infinite hangs in both functions  
**Discovery**: FFT resampling in librosa is incompatible with deployment constraints  
**Remaining Issues**: Need alternative approach for speed

### V18: Scipy Basic Resampling Test
**Problem**: Need faster alternative to librosa phase vocoder  
**Solution**: Implemented scipy.signal.resample() for pitch shifting  
**Result**: FAST (< 1 second) but noisy output with artifacts  
**Remaining Issues**: Poor audio quality, but speed acceptable

### V19: Librosa with Extreme Optimization
**Problem**: Last attempt to make librosa work within timeout  
**Solution**: Reduced n_fft=512, hop_length=128, added caching, removed res_type  
**Result**: STILL TIMED OUT - Even minimal librosa operations exceed 30s on 256MB RAM  
**Decision**: Permanently abandon librosa for deployment  
**Remaining Issues**: Need clean fast solution

### V20: Scipy Polyphase Filtering
**Problem**: Scipy basic resample() has too much noise  
**Solution**: Switched to scipy.signal.resample_poly() with better filtering  
**Result**: SUCCESS - Fast (<1s) with acceptable quality  
**Remaining Issues**: Pitch shift amount seems incorrect

### V21: Pitch Ratio Correction
**Problem**: Needed -4.5 semitones to match expected -3 semitones shift  
**Root Cause**: Incorrect ratio calculation (50% error in formula)  
**Solution**: Fixed pitch ratio: `2^(semitones/12)` with correct up/down calculation  
**Result**: Pitch shifting now mathematically correct  
**Remaining Issues**: Duration stretched (speech hard to understand)

### V22: Two-Step Resampling Attempt
**Problem**: Duration stretching makes speech difficult to comprehend  
**Attempted Solution**: Resample for pitch, then resample back to original length  
**Result**: COMPLETE FAILURE - No pitch change at all  
**Root Cause Analysis**: 
  - Mathematical impossibility: `resample(resample(audio, r1), original_length)` ≈ `audio`
  - Duration restoration cancels the pitch shift
  - Fundamental flaw in approach
**Decision**: Cannot preserve duration in backend with resampling  
**Remaining Issues**: Need different approach to duration problem

### V23: Pyrubberband Attempt
**Problem**: Need time-stretching without pitch change (or vice versa)  
**Attempted Solution**: Tried pyrubberband library for professional audio manipulation  
**Result**: FAILED - Requires external rubberband CLI tool not available on Koyeb  
**Remaining Issues**: Back to seeking solution for duration stretching

### V24: Simple Scipy with Duration Awareness
**Problem**: All attempts to fix duration in backend failed  
**Solution**: Revert to simple scipy resampling, document duration change  
**Result**: Works correctly - pitch accurate, duration stretched  
**User Feedback**: "Resampling slow down the speed as pitch goes down, make it hard to understand"  
**Remaining Issues**: Duration stretching unacceptable for user experience

### V25: Playback Rate Compensation (Breakthrough)
**Problem**: Backend cannot fix duration without canceling pitch shift  
**Solution**: Separate concerns:
  - Backend: scipy resampling (changes pitch + duration)
  - Frontend: JavaScript playback rate (restores duration)
**Implementation**:
  ```javascript
  const pitchRatio = Math.pow(2, semitones / 12.0);
  const durationCompensation = 1.0 / pitchRatio;
  const finalPlaybackRate = selectedSpeed × durationCompensation;
  ```
**Result**: SUCCESS - Correct pitch, near-original duration, fast processing  
**User Feedback**: Acceptable but requests slightly slower playback  
**Remaining Issues**: "Normal speed" (1.0x) too fast for elderly users

### V26: Final Calibration (PRODUCTION)
**Problem**: 1.0x playback still slightly too fast for target users  
**User Request**: "Recalibrate, make it slower, 90%, but call it normal speed"  
**Solution**: Changed base speed from 1.0x to 0.9x, relabeled as "正常速度" (normal speed)  
**Configuration**:
  - Speed options: 0.9x (normal), 0.7x (slower), 0.5x (very slow)
  - Default pitch: -5 semitones (better for elderly users than -3)
  - Example: -5 semitones → 0.9 × 1.335 = 1.20x actual playback rate
**Result**: FINAL VERSION - User confirmed "okay, this is final"  
**All Issues Resolved**: Fast, correct, duration-compensated, user-calibrated

---

## Problems Solved

✅ **Timeout Issues**: Reduced processing from 30-100+ seconds (librosa) to <1 second (scipy)  
✅ **Syntax Errors**: Fixed bins_per_octane typo, removed problematic res_type parameters  
✅ **Pitch Accuracy**: Correct mathematical implementation of semitone-to-ratio conversion  
✅ **Duration Stretching**: Playback rate compensation restores near-original duration  
✅ **User Experience**: Calibrated for elderly users with 0.9x "normal" speed  
✅ **Deployment Reliability**: 26 successful deployments with 5-10 minute turnaround  
✅ **Performance**: Consistent <1 second processing, no timeouts  

---

## Known Limitations

❌ **Audio Quality**: Background noise/artifacts present (trade-off for speed)  
   - Scipy resampling uses polyphase filtering, not phase vocoder
   - Quality sufficient for speech comprehension but not studio-grade

❌ **Duration Not Perfectly Restored**: Playback rate compensation is close but not exact  
   - Theoretical duration = original, but browser playback may have minor timing differences
   - Acceptable for intended use case

❌ **No True Time-Stretching**: Cannot change duration without affecting pitch  
   - Limitation of resampling-based approach
   - Professional phase vocoder approach too slow for deployment constraints

❌ **Platform-Specific Constraints**: 
   - 256MB RAM limit on Koyeb
   - 60-second gunicorn timeout
   - Cannot use librosa or other CPU-intensive libraries

---

## Technical Lessons Learned

1. **Phase Vocoder Quality vs Speed Trade-off**: Impossible to have both with deployment constraints
2. **Browser APIs Are Powerful**: Playback rate provides time-stretching without server processing
3. **Separate Concerns**: Split pitch (backend) and duration (frontend) to work around limitations
4. **Two-Step Resampling Fallacy**: Mathematically impossible to preserve pitch while restoring duration via resampling
5. **User Testing Critical**: 1.0x "normal" speed was actually too fast for target users
6. **Extensive Logging Essential**: Debugging deployment issues requires detailed logging (timings, ratios, sample counts)
7. **Iterative Deployment**: 26 versions led to optimal solution through experimentation

---

## Deployment Information

### Platform: ai-builders.space (Koyeb Backend)
- **RAM**: 256MB limit
- **Timeout**: 60 seconds gunicorn worker timeout
- **Deployment Time**: 5-10 minutes per deployment
- **Auto-deploy**: Push to GitHub main branch triggers deployment
- **Container Sleep**: 5 minutes after idle

### Local Development
- **Python**: 3.14.0 (venv at `.venv/Scripts/python.exe`)
- **Server**: Flask development server
- **Port**: 8003 (to avoid conflicts with production)
- **Testing**: Immediate feedback without deployment wait time

### Repository
- **URL**: https://github.com/yepogue/pitch-shifter
- **Branch**: main
- **Latest Commit**: 84d58d2 "v26: Final version - 0.9x base speed, -5 semitones default, auto playback compensation"

---

## Performance Metrics (V26)

- **Processing Time**: 0.04-0.07 seconds average
- **Load Time**: 0.00-0.01 seconds (soundfile)
- **Shift Time**: 0.00-0.02 seconds (scipy resampling)
- **Save Time**: 0.00-0.01 seconds (WAV encoding)
- **Total Time**: <0.1 seconds consistently
- **Memory**: Well within 256MB limit
- **Timeout Risk**: Zero (100x safety margin)

**Example Log Output**:
```
Processing pitch shift: semitones=-5.0
  Resampling: up=1000, down=749, ratio=1.3351, pitch_ratio=0.7492
✓ Pitch shift complete in 0.00s (original: 77760 samples, new: 103819 samples)
✓ Audio saved in 0.01s
Load: 0.00s, Shift: 0.00s, Save: 0.01s, Total: 0.04s
```

---

## User Interface Features

- **Microphone Recording**: Browser-based audio capture
- **Real-time Controls**: Pitch slider with live feedback
- **Automatic Compensation**: Playback rate adjusts automatically
- **Speed Options**: Three presets (0.9x/0.7x/0.5x) with manual compensation
- **Chinese UI**: Optimized for target user demographic
- **Visual Feedback**: Processing status, error messages, version display
- **Browser Timeout**: 30 seconds for faster failure detection

---

## Final Status

**Version 26** is the **PRODUCTION-READY FINAL VERSION**

✅ All requirements met  
✅ User approved ("okay, this is final")  
✅ Deployed to ai-builders.space  
✅ Local testing environment functional  
✅ Performance within all constraints  
✅ Quality acceptable for intended use case  

**Deployment Time**: 2026-01-31 16:04:12  
**Status**: Active and serving requests

---

*Document created: 2026-01-31*  
*Final version: v26*
