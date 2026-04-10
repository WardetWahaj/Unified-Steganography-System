"""
Database Models for User Management and File Tracking
Tracks users, their RSA keys, and files they've created
"""
import sqlite3
import os
import json
from datetime import datetime
import hashlib

DB_PATH = 'database/stego_system.db'


class Database:
    """SQLite database helper for user and file management"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        # Ensure database directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT DEFAULT '',
                fullname TEXT DEFAULT '',
                password_hash TEXT NOT NULL,
                public_key TEXT NOT NULL,
                private_key TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Files table - tracks which user created the stego file
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                creator_user_id INTEGER NOT NULL,
                creator_public_key TEXT NOT NULL,
                original_secret TEXT NOT NULL,
                encryption_method TEXT DEFAULT 'hybrid',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(creator_user_id) REFERENCES users(id)
            )
        ''')
        
        # File recipients table - tracks which users can decrypt which files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                recipient_user_id INTEGER NOT NULL,
                encrypted_master_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(file_id) REFERENCES files(id),
                FOREIGN KEY(recipient_user_id) REFERENCES users(id),
                UNIQUE(file_id, recipient_user_id)
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        # Audit logs table - tracks all user operations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                status TEXT DEFAULT 'success',
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        
        # Database migrations for existing tables
        try:
            cursor.execute('PRAGMA table_info(files)')
            columns = [col[1] for col in cursor.fetchall()]
            if 'encryption_method' not in columns:
                print("[*] Adding encryption_method column to files table...")
                cursor.execute('ALTER TABLE files ADD COLUMN encryption_method TEXT DEFAULT \'hybrid\'')
                conn.commit()
        except Exception as e:
            print(f"[!] Warning: Could not add encryption_method column: {e}")
        
        # Add status column to users table if it doesn't exist
        try:
            cursor.execute('PRAGMA table_info(users)')
            columns = [col[1] for col in cursor.fetchall()]
            if 'status' not in columns:
                print("[*] Adding status column to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT \'active\'')
                conn.commit()
        except Exception as e:
            print(f"[!] Warning: Could not add status column: {e}")
        
        conn.close()
        print(f"[+] Database initialized at {self.db_path}")
    
    def user_exists(self, username):
        """Check if user exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def create_user(self, username, password_hash, public_key, private_key, email='', fullname=''):
        """Create new user with RSA key pair"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, fullname, password_hash, public_key, private_key)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, fullname, password_hash, public_key, private_key))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            print(f"[+] User '{username}' created with ID {user_id}")
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Username '{username}' already exists")
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def create_session(self, user_id, session_token, expires_at):
        """Create user session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at))
        conn.commit()
        conn.close()
        return True
    
    def get_session_user(self, session_token):
        """Get user from session token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id FROM sessions 
            WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def invalidate_session(self, session_token):
        """Invalidate a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
        conn.commit()
        conn.close()
        return True
    
    def log_operation(self, user_id=None, username=None, action=None, resource=None, status='success', details=None, ip_address=None):
        """Log an operation to the audit log"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_logs (user_id, username, action, resource, status, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, action, resource, status, details, ip_address))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error logging operation: {e}")
    
    def create_file_record(self, file_name, creator_user_id, creator_public_key, original_secret='', encryption_method='hybrid'):
        """Record a created stego file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO files (file_name, creator_user_id, creator_public_key, original_secret, encryption_method)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_name, creator_user_id, creator_public_key, original_secret, encryption_method))
            conn.commit()
            file_id = cursor.lastrowid
            conn.close()
            return file_id
        except Exception as e:
            # Fallback for older database without encryption_method column
            print(f"[!] Warning: Could not insert with encryption_method: {e}")
            try:
                cursor.execute('''
                    INSERT INTO files (file_name, creator_user_id, creator_public_key, original_secret)
                    VALUES (?, ?, ?, ?)
                ''', (file_name, creator_user_id, creator_public_key, original_secret))
                conn.commit()
                file_id = cursor.lastrowid
            finally:
                conn.close()
            return file_id
    
    def get_file_record(self, file_name):
        """Get file record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, u.username 
            FROM files f 
            JOIN users u ON f.creator_user_id = u.id
            WHERE f.file_name = ?
        ''', (file_name,))
        file_record = cursor.fetchone()
        conn.close()
        return dict(file_record) if file_record else None
    
    def get_all_users(self):
        """Get all users (for recipient selection)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, fullname FROM users ORDER BY username')
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    def add_file_recipients(self, file_id, recipient_keys):
        """
        Add encrypted keys for recipients
        
        :param file_id: File ID from files table
        :param recipient_keys: Dict of {recipient_user_id: encrypted_master_key}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for recipient_id, encrypted_key in recipient_keys.items():
                cursor.execute('''
                    INSERT INTO file_recipients (file_id, recipient_user_id, encrypted_master_key)
                    VALUES (?, ?, ?)
                ''', (file_id, recipient_id, encrypted_key))
            conn.commit()
            print(f"[+] Added {len(recipient_keys)} recipients for file {file_id}")
        except Exception as e:
            conn.rollback()
            print(f"[!] Error adding recipients: {e}")
        finally:
            conn.close()
    
    def get_file_recipients(self, file_id):
        """Get all recipients for a file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT recipient_user_id, encrypted_master_key 
            FROM file_recipients 
            WHERE file_id = ?
        ''', (file_id,))
        rows = cursor.fetchall()
        recipients = {row['recipient_user_id']: row['encrypted_master_key'] for row in rows}
        
        # Debug logging
        print(f"[DB] get_file_recipients() - file_id: {file_id}")
        print(f"[DB] Found {len(rows)} recipient entries")
        for row in rows:
            print(f"[DB]   recipient_user_id: {row['recipient_user_id']} (type: {type(row['recipient_user_id']).__name__})")
            if row['encrypted_master_key']:
                print(f"[DB]   encrypted_master_key length: {len(row['encrypted_master_key'])} chars")
        print(f"[DB] Returning recipients dict with keys: {list(recipients.keys())}")
        print(f"[DB] Key types: {[type(k).__name__ for k in recipients.keys()]}")
        
        conn.close()
        return recipients
    
    def get_encrypted_key_for_user(self, file_id, user_id):
        """Get the encrypted master key for a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT encrypted_master_key 
            FROM file_recipients 
            WHERE file_id = ? AND recipient_user_id = ?
        ''', (file_id, user_id))
        result = cursor.fetchone()
        conn.close()
        return result['encrypted_master_key'] if result else None
    
    def get_file_id_by_name(self, file_name):
        """Get file ID by file name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM files WHERE file_name = ?', (file_name,))
        result = cursor.fetchone()
        conn.close()
        return result['id'] if result else None


class UserManager:
    """Manage user authentication and key generation"""
    
    def __init__(self, db=None, key_dir='user_keys'):
        self.db = db or Database()
        self.key_dir = key_dir
        os.makedirs(key_dir, exist_ok=True)
    
    @staticmethod
    def hash_password(password):
        """Hash password with salt"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return (salt + key).hex()
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        try:
            hash_bytes = bytes.fromhex(password_hash)
            salt = hash_bytes[:32]
            key = hash_bytes[32:]
            new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return key == new_key
        except Exception:
            return False
    
    def signup(self, username, password):
        """
        Create new user and generate RSA key pair
        
        :param username: Username
        :param password: Password
        :return: Dict with user_id, username, public_key
        """
        if self.db.user_exists(username):
            raise ValueError(f"Username '{username}' already exists")
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Generate RSA keys
        from crypto.rsa_handler import RSAHandler
        rsa = RSAHandler(key_dir=self.key_dir)
        public_key_path, private_key_path = rsa.generate_keys(key_size=2048)
        
        # Read key files
        with open(public_key_path, 'r') as f:
            public_key = f.read()
        
        with open(private_key_path, 'r') as f:
            private_key = f.read()
        
        # Create user in database
        user_id = self.db.create_user(username, password_hash, public_key, private_key)
        
        return {
            'user_id': user_id,
            'username': username,
            'public_key': public_key,
            'message': f"User '{username}' created successfully with RSA keys"
        }
    
    def login(self, username, password):
        """
        Authenticate user
        
        :param username: Username
        :param password: Password
        :return: Dict with user_id, username, session_token
        """
        user = self.db.get_user_by_username(username)
        
        if not user or not self.verify_password(password, user['password_hash']):
            raise ValueError("Invalid username or password")
        
        # Create session
        import secrets
        from datetime import datetime, timedelta
        
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        self.db.create_session(user['id'], session_token, expires_at)
        
        return {
            'user_id': user['id'],
            'username': user['username'],
            'session_token': session_token,
            'public_key': user['public_key'],
            'private_key': user['private_key']
        }
    
    def get_user_keys(self, username):
        """Get user's RSA keys"""
        user = self.db.get_user_by_username(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        return {
            'username': user['username'],
            'public_key': user['public_key'],
            'private_key': user['private_key']
        }
    
    def sign_up(self, username, email, fullname, password):
        """
        Create new user with email and fullname (Alias for signup with extra fields)
        
        :param username: Username
        :param email: User email
        :param fullname: User full name
        :param password: Password
        :return: Dict with user_id, username, success flag
        """
        try:
            if self.db.user_exists(username):
                return {'success': False, 'error': f"Username '{username}' already exists"}
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Generate RSA keys
            from crypto.rsa_handler import RSAHandler
            rsa = RSAHandler(key_dir=self.key_dir)
            public_key_path, private_key_path = rsa.generate_keys(key_size=2048)
            
            # Read key files
            with open(public_key_path, 'r') as f:
                public_key = f.read()
            
            with open(private_key_path, 'r') as f:
                private_key = f.read()
            
            # Create user in database
            user_id = self.db.create_user(username, password_hash, public_key, private_key, email, fullname)
            
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'public_key': public_key,
                'message': f"User '{username}' created successfully with RSA keys"
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sign_in(self, username_or_email, password):
        """
        Authenticate user by username or email
        
        :param username_or_email: Username or email
        :param password: Password
        :return: Dict with success flag and user info
        """
        try:
            # Try to find user by username or email
            user = self.db.get_user_by_username(username_or_email)
            if not user:
                # Try to find by email
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email = ?', (username_or_email,))
                user_row = cursor.fetchone()
                conn.close()
                user = dict(user_row) if user_row else None
            
            if not user or not self.verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Invalid username/email or password'}
            
            return {
                'success': True,
                'user_id': user['id'],
                'username': user['username'],
                'email': user.get('email', ''),
                'fullname': user.get('fullname', ''),
                'public_key': user['public_key'],
                'private_key': user['private_key'],
                'message': 'Login successful'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def decrypt_private_key(self, user_id, password):
        """
        Get user's private key (verification happens through password check)
        
        :param user_id: User ID
        :param password: User's login password (for verification)
        :return: Private key if password is correct, None otherwise
        """
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return None
            
            # Verify password before returning private key
            if not self.verify_password(password, user['password_hash']):
                return None
            
            # Return the private key (stored as plain PEM text)
            return user.get('private_key')
        except Exception:
            return None
