import hashlib
from datetime import datetime, timedelta
from django.conf import settings
import secrets
import jwt
def hash_password(password):
    salt = secrets.token_hex(16)
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed_password, salt


def verify_password(input_password, stored_hashed_password, salt):
    hashed_input_password = hashlib.sha256((input_password + salt).encode()).hexdigest()

    return hashed_input_password == stored_hashed_password

def generate_jwt_token(user_id):
    now = datetime.utcnow() 
    payload = {
        'user_id': user_id,
        'exp': now + timedelta(days=1), 
        'iat': now - timedelta(seconds=5),  
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def verify_jwt_token(token):
    try:
        print(f"Token received: {token}")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        print(f"Decoded payload: {payload}")

        return payload
    except jwt.ExpiredSignatureError:
        print("Expired signature error")
        return None
    except jwt.exceptions.DecodeError as e:
        print(f"JWT decode error: {str(e)}")
        return None
    except Exception as e:
        print(f"Error decoding JWT token: {str(e)}")
        return None