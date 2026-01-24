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
from pydub import AudioSegment

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size


def pitch_shift_audio(input_path, semitones):
    """
    Change audio pitch (optimized for faster processing)
    
    Args:
        input_path: Input audio file path
        semitones: Pitch change in semitones (negative = lower pitch)
    
    Returns:
        Path to output file
    """
    input_path = Path(input_path)
    
    # Load audio with faster resampling method
    y, sr = librosa.load(str(input_path), sr=None, res_type='kaiser_fast')
    
    # Apply pitch shift with optimized parameters for speed
    y_shifted = librosa.effects.pitch_shift(
        y=y,
        sr=sr,
        n_steps=semitones,
        bins_per_octave=12,
        n_fft=1024,  # Smaller FFT window for faster processing
        hop_length=256  # Smaller hop length for faster processing
    )
    
    # Save output
    output_path = Path(tempfile.gettempdir()) / f"pitched_{input_path.stem}.wav"
    sf.write(str(output_path), y_shifted, sr)
    
    return output_path


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_audio():
    """Process recorded audio from microphone"""
    try:
        # Get pitch shift value
        semitones = float(request.form.get('semitones', -3.0))
        
        # Check if file was uploaded
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        temp_input = Path(tempfile.gettempdir()) / f"input_{file.filename}"
        file.save(str(temp_input))
        
        # Process audio (speed will be adjusted during playback)
        output_path = pitch_shift_audio(temp_input, semitones)
        
        # Clean up input file
        if temp_input.exists():
            temp_input.unlink()
        
        # Return processed audio
        return send_file(
            str(output_path),
            mimetype='audio/wav',
            as_attachment=True,
            download_name='pitched_audio.wav'
        )
    
    except Exception as e:
        import traceback
        print(f"Error processing audio: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Read PORT from environment variable (required for deployment)
    port = int(os.getenv('PORT', '8000'))
    print("Starting web interface...")
    print(f"Open your browser and go to: http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
