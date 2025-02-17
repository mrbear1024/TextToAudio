This is a tool to convert markdown to speech using OpenAI Whisper API.

# virtualenv

```bash
python -m venv venv
source venv/bin/activate
```

# Install

Set OPENAI_API_KEY environment variable on your system terminal

```bash
export OPENAI_API_KEY=your_openai_api_key
```

install requirements
```bash
pip install -r requirements.txt
```

# Run

```bash
python text_to_speech.py <markdown_file_path> [-o <output_file_path>]
```

markdown_file_path: the path to the markdown file to convert
output_file_path: the path to the output audio file (optional)

example:

```bash
python text_to_speech.py test.md -o test.mp3
```
