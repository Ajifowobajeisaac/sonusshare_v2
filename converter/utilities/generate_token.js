const jwt = require('jsonwebtoken');
const fs = require('fs');
const path = require('path');

// Apple Developer account details
const TEAM_ID = '732N38L7AM';
const KEY_ID = '943ZMY4RS6';
const PRIVATE_KEY_PATH = path.join(__dirname, 'apple_auth_key.p8');

try {
  // Read the private key
  const privateKey = fs.readFileSync(PRIVATE_KEY_PATH, 'utf8');

  // Generate token with correct claims
  const token = jwt.sign(
    {
      iss: TEAM_ID, // Your Apple Developer Team ID
      iat: Math.floor(Date.now() / 1000), // Current time in seconds
      exp: Math.floor(Date.now() / 1000) + (60 * 60 * 24 * 180), // 180 days from now
      aud: 'music' // Must be 'music' for MusicKit
    },
    privateKey,
    {
      algorithm: 'ES256', // Required algorithm
      header: {
        alg: 'ES256',
        kid: KEY_ID // Your MusicKit Key ID
      }
    }
  );

  console.log('\nGenerated Developer Token:');
  console.log('=========================');
  console.log(token);
  console.log('\nToken Details:');
  console.log('=============');

  // Decode and display token info
  const decoded = jwt.decode(token, { complete: true });
  console.log('Header:', JSON.stringify(decoded.header, null, 2));
  console.log('Payload:', JSON.stringify(decoded.payload, null, 2));
  console.log('\nExpiration:', new Date(decoded.payload.exp * 1000).toLocaleString());
} catch (error) {
  console.error('Error generating token:', error.message);
  if (error.code === 'ENOENT') {
    console.error(`\nPrivate key file not found at: ${PRIVATE_KEY_PATH}`);
    console.error('Make sure your .p8 file is in the correct location.');
  }
  process.exit(1);
}
