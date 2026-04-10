"""
Command Line Interface for Unified Steganography System
"""
import os
import sys
from core.unified_stego import UnifiedSteganography


class CLI:
    """Command line interface for steganography system"""
    
    def __init__(self):
        self.stego = UnifiedSteganography()
    
    def print_banner(self):
        """Print application banner"""
        print("=" * 70)
        print(" " * 15 + "UNIFIED STEGANOGRAPHY SYSTEM")
        print(" " * 10 + "Audio • Image • Video with RSA Encryption")
        print("=" * 70)
        print()
    
    def print_menu(self):
        """Print main menu"""
        print("\n" + "=" * 70)
        print("MAIN MENU")
        print("=" * 70)
        print("1. Hide File (with encryption)")
        print("2. Extract File (with decryption)")
        print("3. Hide Message (with encryption)")
        print("4. Extract Message (with decryption)")
        print("5. Generate RSA Keys")
        print("6. Exit")
        print("=" * 70)
    
    def get_choice(self):
        """Get user menu choice"""
        try:
            choice = int(input("\nEnter your choice (1-6): "))
            return choice
        except ValueError:
            return 0
    
    def get_file_path(self, prompt):
        """Get and validate file path from user"""
        while True:
            path = input(f"{prompt}: ").strip()
            if os.path.exists(path):
                return path
            else:
                print(f"[!] File not found: {path}")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    return None
    
    def hide_file(self):
        """Hide file workflow"""
        print("\n" + "=" * 70)
        print("HIDE FILE")
        print("=" * 70)
        
        secret_file = self.get_file_path("Enter path to secret file")
        if not secret_file:
            return
        
        cover_file = self.get_file_path("Enter path to cover file (audio/image/video)")
        if not cover_file:
            return
        
        output_file = input("Enter output file path: ").strip()
        
        use_encryption = input("Use encryption? (y/n) [default: y]: ").lower()
        use_encryption = use_encryption != 'n'
        
        password = None
        if use_encryption:
            password = input("Enter encryption password: ")
            if not password:
                print("[!] Password cannot be empty")
                return
        
        try:
            result = self.stego.hide_file(secret_file, cover_file, output_file, 
                                         password, use_encryption)
            print(f"\n[+] SUCCESS! Stego file created: {result}")
        except Exception as e:
            print(f"\n[!] ERROR: {e}")
    
    def extract_file(self):
        """Extract file workflow"""
        print("\n" + "=" * 70)
        print("EXTRACT FILE")
        print("=" * 70)
        
        stego_file = self.get_file_path("Enter path to stego file")
        if not stego_file:
            return
        
        output_file = input("Enter output file path: ").strip()
        
        use_encryption = input("Was the file encrypted? (y/n) [default: y]: ").lower()
        use_encryption = use_encryption != 'n'
        
        password = None
        if use_encryption:
            password = input("Enter decryption password: ")
            if not password:
                print("[!] Password cannot be empty")
                return
        
        try:
            result = self.stego.extract_file(stego_file, output_file, 
                                            password, use_encryption)
            print(f"\n[+] SUCCESS! File extracted: {result}")
        except Exception as e:
            print(f"\n[!] ERROR: {e}")
    
    def hide_message(self):
        """Hide message workflow"""
        print("\n" + "=" * 70)
        print("HIDE MESSAGE")
        print("=" * 70)
        
        message = input("Enter message to hide: ")
        if not message:
            print("[!] Message cannot be empty")
            return
        
        cover_file = self.get_file_path("Enter path to cover file (audio/image/video)")
        if not cover_file:
            return
        
        output_file = input("Enter output file path: ").strip()
        
        use_encryption = input("Use encryption? (y/n) [default: y]: ").lower()
        use_encryption = use_encryption != 'n'
        
        password = None
        if use_encryption:
            password = input("Enter encryption password: ")
            if not password:
                print("[!] Password cannot be empty")
                return
        
        try:
            result = self.stego.hide_message(message, cover_file, output_file, 
                                            password, use_encryption)
            print(f"\n[+] SUCCESS! Stego file created: {result}")
        except Exception as e:
            print(f"\n[!] ERROR: {e}")
    
    def extract_message(self):
        """Extract message workflow"""
        print("\n" + "=" * 70)
        print("EXTRACT MESSAGE")
        print("=" * 70)
        
        stego_file = self.get_file_path("Enter path to stego file")
        if not stego_file:
            return
        
        use_encryption = input("Was the message encrypted? (y/n) [default: y]: ").lower()
        use_encryption = use_encryption != 'n'
        
        password = None
        if use_encryption:
            password = input("Enter decryption password: ")
            if not password:
                print("[!] Password cannot be empty")
                return
        
        try:
            message = self.stego.extract_message(stego_file, password, use_encryption)
            print("\n" + "=" * 70)
            print("EXTRACTED MESSAGE:")
            print("=" * 70)
            print(message)
            print("=" * 70)
        except Exception as e:
            print(f"\n[!] ERROR: {e}")
    
    def generate_keys(self):
        """Generate RSA keys"""
        print("\n" + "=" * 70)
        print("GENERATE RSA KEYS")
        print("=" * 70)
        
        if self.stego.keys_exist():
            overwrite = input("[!] Keys already exist. Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                print("[*] Key generation cancelled")
                return
        
        try:
            pub_key, priv_key = self.stego.generate_keys()
            print(f"\n[+] Keys generated successfully!")
            print(f"[+] Public Key: {pub_key}")
            print(f"[+] Private Key: {priv_key}")
            print("[!] Keep your private key safe!")
        except Exception as e:
            print(f"\n[!] ERROR: {e}")
    
    def run(self):
        """Run the CLI application"""
        self.print_banner()
        
        # Check for RSA keys
        if not self.stego.keys_exist():
            print("[!] WARNING: RSA keys not found!")
            print("[*] RSA encryption will not be available for small files.")
            generate = input("[?] Generate keys now? (y/n): ").lower()
            if generate == 'y':
                self.generate_keys()
        
        while True:
            self.print_menu()
            choice = self.get_choice()
            
            if choice == 1:
                self.hide_file()
            elif choice == 2:
                self.extract_file()
            elif choice == 3:
                self.hide_message()
            elif choice == 4:
                self.extract_message()
            elif choice == 5:
                self.generate_keys()
            elif choice == 6:
                print("\n[*] Thank you for using Unified Steganography System!")
                print("[*] Goodbye!\n")
                sys.exit(0)
            else:
                print("\n[!] Invalid choice! Please select 1-6.")
            
            input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    cli = CLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\n[*] Program interrupted by user")
        print("[*] Goodbye!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
