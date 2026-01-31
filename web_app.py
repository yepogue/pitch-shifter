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
import librosa
import soundfile as sf

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
    
    # Load audio with lower sample rate to save memory (16kHz is good for voice)
    # This significantly reduces memory usage while maintaining speech quality
    y, sr = librosa.load(str(input_path), sr=16000, res_type='kaiser_fast', mono=True)
    
    # Apply pitch shift with very aggressive memory optimization
    y_shifted = librosa.effects.pitch_shift(
        y=y,
        sr=sr,
        n_steps=semitones,
        bins_per_octave=12,
        n_fft=512,  # Even smaller FFT for lower memory
        hop_length=128,  # Smaller hop for lower memory
        res_type='linear'  # Faster, less memory-intensive resampling
    )
    
    # Free original audio from memory immediately
    del y
    gc.collect()
    
    # Save output
    output_path = Path(tempfile.gettempdir()) / f"pitched_{input_path.stem}.wav"
    sf.write(str(output_path), y_shifted, sr)
    
    # Clean up
    del y_shifted
    gc.collect()
    
    return output_path


@app.route('/')
def index():
    """Render main page with optional cache-busting version query."""
    version = request.args.get('v', '20240124-3')
    response = app.make_response(render_template('index.html', version=version))
    # Extra cache busting for HTML
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/process', methods=['POST'])
def process_audio():
    """Process recorded audio from microphone"""
    print("=" * 60)
    print("Received /process request")
    try:
        # Get pitch shift value
        semitones = float(request.form.get('semitones', -3.0))
        print(f"Semitones: {semitones}")
        
        # Check if file was uploaded
        if 'audio' not in request.files:
            print("ERROR: No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        print(f"File received: {file.filename}, content_type: {file.content_type}")
        
        if file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        temp_input = Path(tempfile.gettempdir()) / f"input_{file.filename}"
        print(f"Saving to: {temp_input}")
        file.save(str(temp_input))
        
        # Check file size
        file_size = temp_input.stat().st_size
        print(f"File saved, size: {file_size} bytes")
        
        # Process audio (speed will be adjusted during playback)
        print("Starting audio processing...")
        output_path = pitch_shift_audio(temp_input, semitones)
        print(f"Processing complete: {output_path}")
        
        # Clean up input file
        if temp_input.exists():
            temp_input.unlink()
        
        # Return processed audio
        print("Sending processed file back to client")
        return send_file(
            str(output_path),
            mimetype='audio/wav',
            as_attachment=True,
            download_name='pitched_audio.wav'
        )
    
    except Exception as e:
        import traceback
        error_msg = f"Error processing audio: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        print("=" * 60)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Read PORT from environment variable (required for deployment)
    port = int(os.getenv('PORT', '8000'))
    print("Starting web interface...")
    print(f"Open your browser and go to: http://localhost:{port}")
    # Disable auto-reload to avoid interference
    app.run(debug=False, host='0.0.0.0', port=port)
