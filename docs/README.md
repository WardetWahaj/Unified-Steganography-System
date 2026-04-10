# 🔒 Unified Steganography System

A comprehensive steganography application that combines **audio**, **image**, and **video** steganography with **RSA and AES encryption** for secure data hiding.

## ✨ Features

- **Multi-Format Steganography**:
  - 🎵 **Audio**: WAV files
  - 🖼️ **Image**: PNG, BMP, TIFF, JPG
  - 🎬 **Video**: MP4, AVI, MOV

- **Hybrid Encryption**:
  - 🔐 **RSA Encryption**: For small files (≤245 bytes)
  - 🔒 **AES-256 Encryption**: For larger files
  - 🔑 **Password-based**: Secure password-based key derivation

- **Dual Interface**:
  - 💻 **Command Line Interface (CLI)**: For terminal users
  - 🌐 **Web Interface**: User-friendly browser-based GUI

- **Secure Operations**:
  - Hide files inside media
  - Hide text messages inside media
  - Extract hidden files with decryption
  - Extract hidden messages with decryption
  - Generate RSA key pairs

## 📋 Requirements

- Python 3.8 or higher
- FFmpeg (optional, for video processing)

## 🚀 Installation

### 1. Clone or Download the Project

```bash
cd Unified-Steganography
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
```

**Activate the virtual environment:**

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg (Optional, for Video Processing)

**Windows:**
```bash
scoop install ffmpeg
```
Or download from: https://ffmpeg.org/download.html

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

## 💻 Usage

### Command Line Interface (CLI)

Run the CLI application:

```bash
python main.py
```

**Main Menu Options:**
1. **Hide File** - Hide any file inside audio/image/video with encryption
2. **Extract File** - Extract and decrypt hidden files
3. **Hide Message** - Hide text messages with encryption
4. **Extract Message** - Extract and decrypt hidden messages
5. **Generate RSA Keys** - Create new RSA key pair
6. **Exit**

### Web Interface

1. **Start the web server:**

```bash
python app.py
```

2. **Open your browser and navigate to:**

```
http://localhost:5000
```

3. **Use the web interface:**
   - Navigate between tabs (Hide File, Extract File, Hide Message, Extract Message)
   - Upload your files
   - Set encryption password
   - Download results

## 📖 How It Works

### Steganography Methods

#### Audio Steganography (LSB)
- Modifies the Least Significant Bit (LSB) of audio samples
- Minimal impact on audio quality
- Supports WAV format

#### Image Steganography (LSB)
- Encodes data in the LSB of pixel values
- Imperceptible changes to the image
- Supports PNG, BMP, TIFF, JPG formats

#### Video Steganography (Frame-based)
- Extracts video frames
- Encodes data in frame pixels
- Reassembles video with audio

### Encryption Methods

#### RSA Encryption
- 2048-bit key size
- Used for small files (≤245 bytes)
- Public key encryption

#### AES-256 Encryption
- 256-bit key size
- Used for larger files
- Password-based encryption with SHA-256 key derivation

### Security Features

1. **Hybrid Encryption**: Automatically selects RSA or AES based on file size
2. **Password Protection**: All encrypted data requires a password
3. **Data Integrity**: Includes length markers to ensure complete extraction
4. **Session Management**: Web interface uses secure session handling

## 📁 Project Structure

```
Unified-Steganography/
├── crypto/                      # Encryption modules
│   ├── __init__.py
│   ├── rsa_handler.py          # RSA encryption/decryption
│   ├── aes_handler.py          # AES encryption/decryption
│   └── hybrid_crypto.py        # Hybrid encryption wrapper
├── steganography/               # Steganography modules
│   ├── __init__.py
│   ├── audio_stego.py          # Audio steganography
│   ├── image_stego.py          # Image steganography
│   └── video_stego.py          # Video steganography
├── utils/                       # Utility modules
│   ├── __init__.py
│   └── logging_util.py         # Logging utilities
├── static/                      # Web interface assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   ├── uploads/                # Temporary uploads
│   └── outputs/                # Generated outputs
├── templates/                   # HTML templates
│   └── index.html
├── input/                       # Input files directory
├── output/                      # Output files directory
├── keys/                        # RSA keys storage
│   ├── public.pem              # Generated public key
│   └── private.pem             # Generated private key
├── unified_stego.py            # Main steganography system
├── main.py                     # CLI application
├── app.py                      # Web application
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔑 RSA Keys

### Generating Keys

**CLI:**
```
Select option 5 from main menu
```

**Web Interface:**
```
Click "Generate New Keys" button
```

**Keys Location:**
- Public Key: `keys/public.pem`
- Private Key: `keys/private.pem`

⚠️ **Important**: Keep your private key secure! Anyone with access to it can decrypt your files.

## 🎯 Usage Examples

### Example 1: Hide a Secret Document in an Image

**CLI:**
```
1. Select "Hide File"
2. Enter path to secret document: secret.pdf
3. Enter path to cover image: cover.png
4. Enter output path: stego_image.png
5. Use encryption: y
6. Enter password: MySecurePassword123
```

**Result**: `stego_image.png` contains your encrypted document

### Example 2: Hide a Message in Audio

**Web Interface:**
1. Go to "Hide Message" tab
2. Enter your message: "This is my secret message"
3. Upload cover audio file: `music.wav`
4. Check "Use Encryption"
5. Enter password: `MyPassword`
6. Click "Hide Message"
7. Download the stego audio file

### Example 3: Extract Data from Video

**CLI:**
```
1. Select "Extract File"
2. Enter stego file path: stego_video.mp4
3. Enter output path: extracted_data.zip
4. File encrypted: y
5. Enter password: MySecurePassword123
```

## ⚙️ Configuration

### File Size Limits

- **Web Interface**: 100MB max upload size (configurable in `app.py`)
- **CLI**: Limited by available memory

### Supported Formats

**Audio:**
- Input: WAV (recommended), MP3, FLAC, AIFF
- Output: WAV

**Image:**
- Input/Output: PNG, BMP, TIFF, JPG (PNG recommended for lossless)

**Video:**
- Input/Output: MP4, AVI, MOV (requires FFmpeg)

## 🔧 Troubleshooting

### Video Processing Issues

**Problem**: "FFmpeg not found" error

**Solution**: Install FFmpeg (see Installation section)

### Large File Issues

**Problem**: "Data too large" error

**Solution**: Use a larger cover file or split your data

### Decryption Fails

**Problem**: "Decryption failed" error

**Solutions:**
- Verify you're using the correct password
- Ensure RSA keys are available (for RSA-encrypted files)
- Check that the file was actually encrypted

### OpenCV Video Codec Issues

**Problem**: Cannot read video file

**Solutions:**
- Convert video to MP4 format
- Install additional codecs
- Use FFmpeg for extraction (automatic fallback)

## 🛡️ Security Considerations

1. **Password Strength**: Use strong passwords (12+ characters, mixed case, numbers, symbols)
2. **Key Protection**: Never share your private RSA key
3. **Secure Deletion**: Securely delete original files after hiding
4. **Cover File Quality**: Use high-quality cover files for better capacity
5. **Transmission**: Use secure channels to share passwords separately

## 📝 License

This project is provided for educational purposes.

## 👥 Credits

Combined and enhanced from:
- Audio Steganography CLI
- Data Security using Cryptography and Steganography

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional steganography algorithms
- More encryption methods
- Enhanced UI/UX
- Mobile support
- Additional file format support

## 📧 Support

For issues and questions:
1. Check the Troubleshooting section
2. Review the documentation
3. Check existing issues

## 🎓 Educational Use

This tool is designed for:
- Learning about steganography
- Understanding encryption
- Cybersecurity education
- Research purposes

**⚠️ Use responsibly and ethically!**

## 📚 References

- **Steganography**: The art of hiding information within other information
- **LSB**: Least Significant Bit steganography technique
- **RSA**: Rivest–Shamir–Adleman public-key cryptosystem
- **AES**: Advanced Encryption Standard

---

**Version**: 1.0.0  
**Last Updated**: 2025  
**Status**: Production Ready ✅
