import os
import re
import openai
import markdown
import argparse
import glob
from pydub import AudioSegment
from bs4 import BeautifulSoup
from typing import List

# Set OpenAI API key
# 设置OpenAI API密钥
openai.api_key = os.getenv("OPENAI_API_KEY")

def split_text(text: str, max_length: int = 4000) -> List[str]:
    """
    Split text into chunks of maximum length
    将文本分割成最大长度的块
    
    Args:
        text (str): Input text
        max_length (int): Maximum length of each chunk
        
    Returns:
        List[str]: List of text chunks
    """
    # Split by sentences to avoid cutting in the middle of a sentence
    # 按句子分割以避免在句子中间切断
    sentences = re.split(r'([。！？.!?])', text)
    chunks = []
    current_chunk = ""
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        # Add the punctuation mark back if it exists
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]
            
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def convert_text_to_speech(text_content, output_file="output.mp3"):
    """
    Convert text content to speech using OpenAI Whisper API
    将文本内容转换为语音使用OpenAI Whisper API
    
    Args:
        text_content (str): Input text or markdown content
        output_file (str): Output audio file path
    """
    # Process markdown if the content is markdown
    # 如果内容是markdown格式则进行处理
    if text_content.startswith('#') or '**' in text_content or '*' in text_content:
        # Convert markdown to HTML
        html = markdown.markdown(text_content)
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Replace images with placeholder text
        # 将图片替换为占位符文本
        for img in soup.find_all('img'):
            img.replace_with("请看文稿图片")
            
        # Replace links with placeholder text
        # 将链接替换为占位符文本
        for link in soup.find_all('a'):
            link.replace_with("请看文稿链接")
            
        # Get clean text
        text_content = soup.get_text()
    
    # Remove extra whitespace and newlines
    # 删除多余的空格和换行
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # Split text into chunks
    # 将文本分割成块
    chunks = split_text(text_content)
    
    try:
        # Process each chunk and save to separate files
        # 处理每个块并保存到单独的文件
        for i, chunk in enumerate(chunks):
            # Generate output filename for chunk
            # 为每个块生成输出文件名
            base, ext = os.path.splitext(output_file)
            chunk_file = f"{base}_part{i+1}{ext}"
            
            # Call OpenAI Text-to-Speech API
            # 调用OpenAI文字转语音API
            response = openai.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=chunk
            )
            
            # Save the audio file
            # 保存音频文件
            response.stream_to_file(chunk_file)
            print(f"Audio file saved as {chunk_file}")
            
    except Exception as e:
        print(f"Error occurred during text-to-speech conversion: {str(e)}")
        raise

def convert_file_to_speech(file_path, output_file=None):
    """
    Convert a file's content to speech
    将文件内容转换为语音
    
    Args:
        file_path (str): Path to input text/markdown file
        output_file (str): Optional output audio file path
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
        
    # Generate output filename if not provided
    # 如果未提供输出文件名则自动生成
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file = f"{base_name}_audio.mp3"
    
    # Read file content
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convert to speech
    # 转换为语音
    convert_text_to_speech(content, output_file)

    
def merge_audio_files(input_pattern, output_file):
    """
    Merge multiple audio files into a single file
    将多个音频文件合并成单个文件
    
    Args:
        input_pattern (str): Pattern to match input audio files (e.g. "chunk_*.mp3")
        output_file (str): Path for merged output audio file
    """
    try:
        # Get list of audio files matching pattern
        # 获取匹配模式的音频文件列表
        audio_files = sorted(glob.glob(input_pattern))
        
        if not audio_files:
            raise ValueError(f"No audio files found matching pattern: {input_pattern}")
            
        # Create audio segment for first file
        # 为第一个文件创建音频片段
        combined = AudioSegment.from_mp3(audio_files[0])
        
        # Append remaining files
        # 追加剩余文件
        for audio_file in audio_files[1:]:
            segment = AudioSegment.from_mp3(audio_file)
            combined += segment
            
        # Export merged audio
        # 导出合并的音频
        combined.export(output_file, format="mp3")
        print(f"Merged audio saved to: {output_file}")
        
    except Exception as e:
        print(f"Error merging audio files: {str(e)}")
        raise

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="Convert markdown file to speech")
    parser.add_argument("file_path", help="Path to the markdown file to convert")
    parser.add_argument("-o", "--output", help="Output audio file path (optional)")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 调用转换函数
    convert_file_to_speech(args.file_path, args.output)
    # Merge the generated audio chunks
    # 合并生成的音频片段
    try:
        chunk_pattern = "*_audio_part*.mp3"
        merged_output = "merged_output.mp3"
        merge_audio_files(chunk_pattern, merged_output)
        print(f"Successfully merged audio chunks into: {merged_output}")
        
        # Clean up individual chunk files
        # 清理单个音频片段文件
        for chunk_file in glob.glob(chunk_pattern):
            os.remove(chunk_file)
    except Exception as e:
        print(f"Error merging audio chunks: {str(e)}")
        raise
