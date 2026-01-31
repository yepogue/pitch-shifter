#!/usr/bin/env python3
"""
语音降调助听器网页界面
帮助老年人通过降低音调来更清晰地听到对话
直接从麦克风录音
"""

import os
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
import logging
import time

# Configure logging BEFORE importing heavy libraries
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Pre-load heavy audio libraries at startup to speed up first request
logger.info("🔧 Pre-loading audio libraries...")
import_start = time.time()
import librosa
import soundfile as sf
import numpy as np  # Pre-import to avoid lazy loading
logger.info(f"✅ Libraries loaded in {time.time() - import_start:.2f}s")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Reduced to 10MB for memory constraints
# Disable static caching during dev to avoid stale HTML
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True


def pitch_shift_audio(input_path, semitones):
    """
    Change audio pitch (optimized for low memory environments)
    
    Args:
        input_path: Input audio file path
        semitones: Pitch change in semitones (negative = lower pitch)
    
    Returns:
        Path to output file
    """
    import gc
    input_path = Path(input_path)
    
    logger.info(f"🎵 Starting pitch shift: {input_path.name}, semitones={semitones}")
    start_time = time.time()
    
    # Load audio with lower sample rate to save memory (16kHz is good for voice)
    # This significantly reduces memory usage while maintaining speech quality
    logger.info("📂 Loading audio file...")
    y, sr = librosa.load(str(input_path), sr=16000, res_type='fft', mono=True)
    logger.info(f"✓ Audio loaded: {len(y)} samples, sample rate={sr}Hz, duration={len(y)/sr:.2f}s")
    
    # Apply pitch shift with very aggressive memory optimization
    logger.info(f"🔄 Applying pitch shift ({semitones} semitones)...")
    y_shifted = librosa.effects.pitch_shift(
        y=y,
        sr=sr,
        n_steps=semitones,
        bins_per_octave=12,
        n_fft=512,  # Even smaller FFT for lower memory
        hop_length=128,  # Smaller hop for lower memory
        res_type='fft'  # Use FFT-based resampling (no external deps needed)
    )
    logger.info("✓ Pitch shift complete")
    
    # Free original audio from memory immediately
    del y
    gc.collect()
    
    # Save output
    output_path = Path(tempfile.gettempdir()) / f"pitched_{input_path.stem}.wav"
    logger.info(f"💾 Saving to: {output_path}")
    sf.write(str(output_path), y_shifted, sr)
    
    elapsed = time.time() - start_time
    logger.info(f"✅ Processing complete in {elapsed:.2f}s, output size: {output_path.stat().st_size} bytes")
    
    # Clean up
    del y_shifted
    gc.collect()
    
    return output_path


@app.route('/')
def index():
    """Render main page with optional cache-busting version query."""
    version = request.args.get('v', '20260130-7')
    response = app.make_response(render_template('index.html', version=version))
    # Extra cache busting for HTML
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/process', methods=['POST'])
def process_audio():
    """Process recorded audio from microphone"""
    logger.info("=" * 60)
    logger.info("📥 Received /process request")
    try:
        # Get pitch shift value
        semitones = float(request.form.get('semitones', -3.0))
        logger.info(f"🎚️ Semitones parameter: {semitones}")
        
        # Check if file was uploaded
        if 'audio' not in request.files:
            logger.error("❌ No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        logger.info(f"📎 File received: filename='{file.filename}', content_type='{file.content_type}'")
        
        if file.filename == '':
            logger.error("❌ Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        temp_input = Path(tempfile.gettempdir()) / f"input_{file.filename}"
        logger.info(f"💾 Saving uploaded file to: {temp_input}")
        file.save(str(temp_input))
        
        # Check file size
        file_size = temp_input.stat().st_size
        logger.info(f"✓ File saved successfully, size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        if file_size == 0:
            logger.error("❌ Uploaded file is empty (0 bytes)")
            return jsonify({'error': 'Uploaded file is empty'}), 400
        
        # Process audio (speed will be adjusted during playback)
        logger.info("🚀 Starting audio processing...")
        output_path = pitch_shift_audio(temp_input, semitones)
        logger.info(f"✅ Processing complete: {output_path}")
        
        # Clean up input file
        if temp_input.exists():
            temp_input.unlink()
            logger.info(f"🗑️ Cleaned up input file: {temp_input}")
        
        # Return processed audio
        logger.info("📤 Sending processed file back to client")
        logger.info("=" * 60)
        return send_file(
            str(output_path),
            mimetype='audio/wav',
            as_attachment=True,
            download_name='pitched_audio.wav'
        )
    
    except Exception as e:
        import traceback
        error_msg = f"❌ Error processing audio: {str(e)}"
        logger.error(error_msg)
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.info("=" * 60)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Read PORT from environment variable (required for deployment)
    port = int(os.getenv('PORT', '8002'))
    logger.info("🚀 Starting web interface...")
    logger.info(f"🌐 Open your browser and go to: http://localhost:{port}")
    logger.info("=" * 60)
    # Disable auto-reload to avoid interference
    app.run(debug=False, host='0.0.0.0', port=port)
