import hashlib
import secrets
import base64
from typing import Optional


class PasswordManager:
    def __init__(self, salt_length: int = 32):
        self.salt_length = salt_length
    
    def generate_salt(self) -> str:
        """Generate a random salt for password hashing"""
        return base64.b64encode(secrets.token_bytes(self.salt_length)).decode('utf-8')
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash a password with salt"""
        if salt is None:
            salt = self.generate_salt()
        
        # Combine password and salt
        salted_password = password + salt
        
        # Hash using SHA-256
        password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
        
        return password_hash, salt
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify a password against stored hash"""
        computed_hash, _ = self.hash_password(password, salt)
        return computed_hash == stored_hash
    
    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def check_password_strength(self, password: str) -> dict:
        """Check password strength and return score"""
        score = 0
        feedback = []
        
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters")
        
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Include lowercase letters")
        
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Include uppercase letters")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Include numbers")
        
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            feedback.append("Include special characters")
        
        strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
        strength = strength_levels[min(score, 4)]
        
        return {
            'score': score,
            'max_score': 5,
            'strength': strength,
            'feedback': feedback
        }


if __name__ == "__main__":
    pm = PasswordManager()
    
    # Test password hashing
    password = "my_secure_password123"
    hashed, salt = pm.hash_password(password)
    
    print(f"Original: {password}")
    print(f"Hashed: {hashed[:20]}...")
    print(f"Verification: {pm.verify_password(password, hashed, salt)}")
    
    # Generate secure password
    new_password = pm.generate_password(16)
    print(f"Generated password: {new_password}")
    
    # Check strength
    strength = pm.check_password_strength(new_password)
    print(f"Strength: {strength['strength']} ({strength['score']}/{strength['max_score']})")