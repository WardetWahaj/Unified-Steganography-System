"""
Flask Web Application for Unified Steganography System
"""
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import secrets
import shutil
from core.unified_stego import UnifiedSteganography


app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 100MB max

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'outputs')
KEY_FOLDER = os.path.join(BASE_DIR, 'keys')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(KEY_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Initialize steganography system
stego = UnifiedSteganography(key_dir=KEY_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'audio': {'wav', 'mp3', 'flac', 'aiff'},
    'image': {'png', 'bmp', 'tiff', 'jpg', 'jpeg'},
    'video': {'mp4', 'avi', 'mov', 'mkv'}
}


def allowed_file(filename, file_type='all'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'all':
        all_exts = set()
        for exts in ALLOWED_EXTENSIONS.values():
            all_exts.update(exts)
        return ext in all_exts
    else:
        return ext in ALLOWED_EXTENSIONS.get(file_type, set())


def get_session_id():
    """Get or create session ID"""
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    return session['session_id']


def cleanup_session_files(session_id):
    """Clean up files for a session"""
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            if filename.startswith(session_id):
                try:
                    os.remove(os.path.join(folder, filename))
                except:
                    pass


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', keys_exist=stego.keys_exist())


@app.route('/api/generate-keys', methods=['POST'])
def generate_keys():
    """Generate RSA keys"""
    try:
        pub_key, priv_key = stego.generate_keys()
        return jsonify({
            'success': True,
            'message': 'RSA keys generated successfully',
            'public_key': pub_key,
            'private_key': priv_key
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hide-file', methods=['POST'])
def hide_file():
    """Hide file in cover media"""
    try:
        session_id = get_session_id()
        
        # Get files
        if 'secret_file' not in request.files or 'cover_file' not in request.files:
            return jsonify({'success': False, 'error': 'Missing files'}), 400
        
        secret_file = request.files['secret_file']
        cover_file = request.files['cover_file']
        
        if secret_file.filename == '' or cover_file.filename == '':
            return jsonify({'success': False, 'error': 'No files selected'}), 400
        
        # Get parameters
        password = request.form.get('password', '')
        use_encryption = request.form.get('use_encryption', 'true').lower() == 'true'
        
        if use_encryption and not password:
            return jsonify({'success': False, 'error': 'Password required for encryption'}), 400
        
        # Check cover file type
        if not allowed_file(cover_file.filename):
            return jsonify({'success': False, 'error': 'Unsupported cover file format'}), 400
        
        # Save uploaded files
        secret_filename = secure_filename(secret_file.filename)
        cover_filename = secure_filename(cover_file.filename)
        
        secret_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_secret_{secret_filename}")
        cover_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_cover_{cover_filename}")
        
        secret_file.save(secret_path)
        cover_file.save(cover_path)
        
        # Generate output filename
        cover_ext = os.path.splitext(cover_filename)[1]
        output_filename = f"{session_id}_stego{cover_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Hide file
        stego.hide_file(secret_path, cover_path, output_path, 
                       password if use_encryption else None, use_encryption)
        
        # Cleanup input files
        os.remove(secret_path)
        os.remove(cover_path)
        
        return jsonify({
            'success': True,
            'message': 'File hidden successfully',
            'output_file': output_filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extract-file', methods=['POST'])
def extract_file():
    """Extract hidden file from stego media"""
    try:
        session_id = get_session_id()
        
        # Get file
        if 'stego_file' not in request.files:
            return jsonify({'success': False, 'error': 'Missing file'}), 400
        
        stego_file = request.files['stego_file']
        
        if stego_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get parameters
        password = request.form.get('password', '')
        use_encryption = request.form.get('use_encryption', 'true').lower() == 'true'
        output_name = request.form.get('output_name', 'extracted_file.bin')
        
        if use_encryption and not password:
            return jsonify({'success': False, 'error': 'Password required for decryption'}), 400
        
        # Check file type
        if not allowed_file(stego_file.filename):
            return jsonify({'success': False, 'error': 'Unsupported file format'}), 400
        
        # Save uploaded file
        stego_filename = secure_filename(stego_file.filename)
        stego_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_stego_{stego_filename}")
        stego_file.save(stego_path)
        
        # Generate output filename
        output_filename = f"{session_id}_{secure_filename(output_name)}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Extract file
        stego.extract_file(stego_path, output_path,
                          password if use_encryption else None, use_encryption)
        
        # Cleanup input file
        os.remove(stego_path)
        
        return jsonify({
            'success': True,
            'message': 'File extracted successfully',
            'output_file': output_filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hide-message-whatsapp', methods=['POST'])
def hide_message_whatsapp():
    """Hide message optimized for WhatsApp transmission"""
    try:
        session_id = get_session_id()
        
        # Get parameters
        message = request.form.get('message', '')
        password = request.form.get('password', '')
        use_encryption = request.form.get('use_encryption', 'true').lower() == 'true'
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        if use_encryption and not password:
            return jsonify({'success': False, 'error': 'Password required for encryption'}), 400
        
        # Get cover file
        if 'cover_file' not in request.files:
            return jsonify({'success': False, 'error': 'Missing cover file'}), 400
        
        cover_file = request.files['cover_file']
        
        if cover_file.filename == '':
            return jsonify({'success': False, 'error': 'No cover file selected'}), 400
        
        # Check if it's an image (WhatsApp optimization works best with images)
        if not allowed_file(cover_file.filename, 'image'):
            return jsonify({'success': False, 'error': 'WhatsApp optimization requires image files'}), 400
        
        # Save uploaded file
        cover_filename = secure_filename(cover_file.filename)
        cover_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_cover_{cover_filename}")
        cover_file.save(cover_path)
        
        # Use WhatsApp-optimized steganography
        from steganography.transmission_robust_stego import WhatsAppRobustSteganography
        whatsapp_stego = WhatsAppRobustSteganography()
        
        # Prepare data
        data = message.encode('utf-8')
        
        if use_encryption and password:
            print("[*] Encrypting message for WhatsApp transmission...")
            data, method = stego.crypto.encrypt_data(data, password, use_rsa=True)
            print(f"[+] Encryption method: {method}")
        
        # Generate output filename
        stego_filename = f"{session_id}_whatsapp_stego_{cover_filename.rsplit('.', 1)[0]}.jpg"
        stego_path = os.path.join(OUTPUT_FOLDER, stego_filename)
        
        # Hide message using WhatsApp-optimized method
        whatsapp_stego.encode_for_whatsapp(cover_path, stego_path, data)
        
        # Cleanup input file
        os.remove(cover_path)
        
        return jsonify({
            'success': True,
            'message': 'Message hidden successfully with WhatsApp optimization',
            'stego_file': stego_filename,
            'download_url': f'/api/download/{stego_filename}',
            'method': 'WhatsApp-optimized transmission-robust steganography',
            'note': 'This image is optimized to survive WhatsApp compression'
        })
        
    except Exception as e:
        print(f"WhatsApp hide message error: {e}")
        # Cleanup on error
        for path in [cover_path if 'cover_path' in locals() else None,
                     stego_path if 'stego_path' in locals() else None]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hide-message', methods=['POST'])
def hide_message():
    """Hide message in cover media"""
    try:
        session_id = get_session_id()
        
        # Get file
        if 'cover_file' not in request.files:
            return jsonify({'success': False, 'error': 'Missing cover file'}), 400
        
        cover_file = request.files['cover_file']
        
        if cover_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get parameters
        message = request.form.get('message', '')
        password = request.form.get('password', '')
        use_encryption = request.form.get('use_encryption', 'true').lower() == 'true'
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        if use_encryption and not password:
            return jsonify({'success': False, 'error': 'Password required for encryption'}), 400
        
        # Check file type
        if not allowed_file(cover_file.filename):
            return jsonify({'success': False, 'error': 'Unsupported file format'}), 400
        
        # Save uploaded file
        cover_filename = secure_filename(cover_file.filename)
        cover_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_cover_{cover_filename}")
        cover_file.save(cover_path)
        
# Generate output filename - Enhanced WhatsApp method converts to JPEG
        cover_ext = os.path.splitext(cover_filename)[1]
        if cover_ext.lower() in ['.png', '.bmp', '.tiff']:
            # Enhanced WhatsApp method converts these to JPEG for transmission robustness
            output_filename = f"{session_id}_stego.jpg"
        else:
            output_filename = f"{session_id}_stego{cover_ext}"
        
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Hide message
        actual_output = stego.hide_message(message, cover_path, output_path, 
                                          password if use_encryption else None, use_encryption)
        
        # Get the actual output filename (in case the method changed the extension)
        actual_filename = os.path.basename(actual_output)
        
        # Cleanup input file
        os.remove(cover_path)
        
        return jsonify({
            'success': True,
            'message': 'Message hidden successfully (optimized for transmission)',
            'output_file': actual_filename,
            'download_url': f'/api/download/{actual_filename}',
            'method': 'Enhanced WhatsApp Method - transmission robust'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extract-message', methods=['POST'])
def extract_message():
    """Extract hidden message from stego media with enhanced error handling"""
    try:
        session_id = get_session_id()
        
        # Get file
        if 'stego_file' not in request.files:
            return jsonify({'success': False, 'error': 'Missing file'}), 400
        
        stego_file = request.files['stego_file']
        
        if stego_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get parameters
        password = request.form.get('password', '')
        use_encryption = request.form.get('use_encryption', 'true').lower() == 'true'
        
        if use_encryption and not password:
            return jsonify({'success': False, 'error': 'Password required for decryption'}), 400
        
        # Check file type
        if not allowed_file(stego_file.filename):
            return jsonify({'success': False, 'error': 'Unsupported file format'}), 400
        
        # Save uploaded file
        stego_filename = secure_filename(stego_file.filename)
        stego_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_stego_{stego_filename}")
        stego_file.save(stego_path)
        
        # Enhanced extraction with multiple attempts
        extracted_message = None
        extraction_method = None
        
        try:
            # First try with standard extraction
            extracted_message = stego.extract_message(stego_path,
                                                      password if use_encryption else None,
                                                      use_encryption)
            extraction_method = "Standard extraction"
            
        except Exception as standard_error:
            print(f"[!] Standard extraction failed: {standard_error}")
            
            # If standard fails and it's an image, try direct robust methods
            if stego_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                from steganography.transmission_robust_stego import TransmissionRobustSteganography, WhatsAppRobustSteganography
                
                # Try WhatsApp-robust method
                try:
                    whatsapp_stego = WhatsAppRobustSteganography()
                    raw_data = whatsapp_stego.decode_from_whatsapp(stego_path)
                    
                    if use_encryption and password:
                        raw_data = stego.crypto.decrypt_data(raw_data, password, method='AUTO')
                    
                    extracted_message = raw_data.decode('utf-8', errors='ignore')
                    extraction_method = "WhatsApp-robust extraction"
                    
                except Exception as whatsapp_error:
                    print(f"[!] WhatsApp-robust extraction failed: {whatsapp_error}")
                    
                    # Try ultra-robust method
                    try:
                        ultra_stego = TransmissionRobustSteganography()
                        raw_data = ultra_stego.decode(stego_path)
                        
                        if use_encryption and password:
                            raw_data = stego.crypto.decrypt_data(raw_data, password, method='AUTO')
                        
                        extracted_message = raw_data.decode('utf-8', errors='ignore')
                        extraction_method = "Ultra-robust extraction"
                        
                    except Exception as ultra_error:
                        print(f"[!] Ultra-robust extraction failed: {ultra_error}")
                        # Re-raise the original error if all methods fail
                        raise standard_error
            else:
                # For non-image files, re-raise the original error
                raise standard_error
        
        # Cleanup input file
        if os.path.exists(stego_path):
            os.remove(stego_path)
        
        if extracted_message is not None:
            return jsonify({
                'success': True,
                'message': f'Message extracted successfully using {extraction_method}',
                'extracted_message': extracted_message,
                'extraction_method': extraction_method
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not extract message - file may be corrupted or not contain hidden data'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download output file"""
    try:
        session_id = get_session_id()
        
        # Security check: only allow downloading files from current session
        if not filename.startswith(session_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Get original filename (remove session prefix)
        download_name = filename[len(session_id) + 1:]
        
        return send_file(file_path, as_attachment=True, download_name=download_name)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Cleanup session files"""
    try:
        session_id = get_session_id()
        cleanup_session_files(session_id)
        return jsonify({'success': True, 'message': 'Files cleaned up'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-robust', methods=['POST'])
def test_robust_steganography():
    """Test robust steganography methods"""
    try:
        import tempfile
        from steganography.robust_image_stego import RobustImageSteganography
        from PIL import Image
        
        # Create test image
        test_img = Image.new('RGB', (800, 600), color='lightblue')
        temp_cover = os.path.join(tempfile.gettempdir(), 'test_cover.png')
        test_img.save(temp_cover)
        
        # Test data
        test_message = "🔒 Robust steganography test - this should survive compression! 🚀"
        test_data = test_message.encode('utf-8')
        
        robust_stego = RobustImageSteganography()
        results = {}
        
        # Test different methods
        for method in ['dct', 'metadata', 'hybrid']:
            try:
                # Encode
                temp_stego = os.path.join(tempfile.gettempdir(), f'test_stego_{method}.jpg')
                robust_stego.encode(temp_cover, temp_stego, test_data, method=method)
                
                # Decode
                decoded_data = robust_stego.decode(temp_stego, method=method)
                decoded_message = decoded_data.decode('utf-8')
                
                results[method] = {
                    'success': decoded_message == test_message,
                    'message': f"Method {method}: {'Success' if decoded_message == test_message else 'Failed'}"
                }
                
                # Cleanup
                if os.path.exists(temp_stego):
                    os.remove(temp_stego)
                    
            except Exception as e:
                results[method] = {
                    'success': False,
                    'message': f"Method {method} failed: {str(e)}"
                }
        
        # Cleanup
        if os.path.exists(temp_cover):
            os.remove(temp_cover)
        
        return jsonify({
            'success': True,
            'message': 'Robust steganography test completed',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Test failed: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'Steganography Analysis',
            'version': '1.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    import socket
    
    # Get local IP address
    def get_local_ip():
        try:
            # Create a socket to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "localhost"
    
    local_ip = get_local_ip()
    
    print("=" * 70)
    print(" " * 15 + "UNIFIED STEGANOGRAPHY SYSTEM")
    print(" " * 10 + "Audio • Image • Video with RSA Encryption")
    print("=" * 70)
    print("\n[*] Starting web server...")
    print(f"[*] Local Access:    http://localhost:5000")
    print(f"[*] Network Access:  http://{local_ip}:5000")
    print("\n[!] For mobile devices on same WiFi:")
    print(f"    Update Flutter app baseUrl to: http://{local_ip}:5000")
    print("\n[*] Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
