#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import jwt
    print("JWT module imported successfully")
    print("JWT version:", jwt.__version__)
    
    # Test JWT encode
    payload = {'test': 'data'}
    secret = 'test-secret'
    token = jwt.encode(payload, secret, algorithm='HS256')
    print("JWT encode test successful:", token)
    
    # Test JWT decode
    decoded = jwt.decode(token, secret, algorithms=['HS256'])
    print("JWT decode test successful:", decoded)
    
except ImportError as e:
    print("JWT import failed:", e)
except Exception as e:
    print("JWT test failed:", e)
