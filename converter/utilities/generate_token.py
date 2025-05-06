import jwt
import time
from pathlib import Path

def generate_token():
    # Your credentials
    key_id = 'WTM4GAXM4P'
    team_id = '732N38L7AM'
    private_key_path = Path(__file__).parent / 'apple_auth_key.p8'
    
    # Read the private key
    with open(private_key_path, 'r') as key_file:
        private_key = key_file.read()
    
    # Generate the token
    headers = {
        'alg': 'ES256',
        'kid': key_id
    }
    
    payload = {
        'iss': team_id,
        'iat': int(time.time()),
        'exp': int(time.time() + 15777000)  # 6 months from now
    }
    
    # Generate the token
    token = jwt.encode(
        payload,
        private_key,
        algorithm='ES256',
        headers=headers
    )
    
    print("Generated Developer Token:")
    print(token)
    print("\nThis token is valid for 6 months.")
    return token

if __name__ == '__main__':
    generate_token() 
