#!/usr/bin/env python3
"""
简单的变声器脚本
降低音调但保持速度不变
"""

import argparse
import os
import sys
from pathlib import Path

import librosa
import soundfile as sf
from pydub import AudioSegment


def convert_m4a_to_wav(m4a_path):
    """将m4a文件转换为wav格式（librosa需要）"""
    audio = AudioSegment.from_file(m4a_path, format="m4a")
    wav_path = m4a_path.with_suffix('.temp.wav')
    audio.export(wav_path, format="wav")
    return wav_path


def pitch_shift_audio(input_path, output_path, semitones):
    """
    改变音频音调但不改变速度
    
    Args:
        input_path: 输入音频文件路径
        output_path: 输出音频文件路径
        semitones: 音调变化量（半音数），负数表示降低音调
    """
    # 如果是m4a文件，先转换为wav
    # wav文件可以直接用librosa加载，不需要转换
    temp_wav = None
    if input_path.suffix.lower() == '.m4a':
        print(f"正在转换 {input_path} 为临时wav格式...")
        temp_wav = convert_m4a_to_wav(input_path)
        audio_path = temp_wav
    else:
        # wav等格式可以直接处理
        audio_path = input_path
    
    # 加载音频文件（使用更快的res_type）
    print(f"正在加载音频文件: {audio_path}")
    y, sr = librosa.load(str(audio_path), sr=None, res_type='soxr_hq')
    
    # 应用音调变换（负值表示降低音调）
    # 使用更快的参数：较小的n_fft和hop_length可以加快处理速度
    print(f"正在应用音调变换: {semitones} 半音...")
    y_shifted = librosa.effects.pitch_shift(
        y=y,
        sr=sr,
        n_steps=semitones,
        bins_per_octave=12,
        n_fft=2048,  # 减小FFT窗口大小以加快速度
        hop_length=512  # 减小hop长度以加快速度
    )
    
    # 保存处理后的音频
    print(f"正在保存到: {output_path}")
    sf.write(str(output_path), y_shifted, sr)
    
    # 清理临时文件
    if temp_wav and temp_wav.exists():
        temp_wav.unlink()
        print("已清理临时文件")
    
    print("完成！")


def main():
    parser = argparse.ArgumentParser(
        description='变声器：降低音调但保持速度不变'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='输入音频文件路径（支持m4a等格式）'
    )
    parser.add_argument(
        '-s', '--semitones',
        type=float,
        default=-3.0,
        help='音调变化量（半音数），负数表示降低音调。默认: -3.0（降低3个半音）'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出文件路径（默认：输入文件名_pitched.wav）'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    
    # 检查输入文件是否存在
    if not input_path.exists():
        print(f"错误：文件不存在: {input_path}")
        sys.exit(1)
    
    # 确定输出文件路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_pitched.wav"
    
    # 执行音调变换
    try:
        pitch_shift_audio(input_path, output_path, args.semitones)
        print(f"\n处理完成！输出文件: {output_path}")
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
