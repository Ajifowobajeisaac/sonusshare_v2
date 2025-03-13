# SonusShare

SonusShare is a web application that enables seamless playlist conversion between different music streaming platforms.

## Features

### Currently Supported
- Convert Apple Music playlists to Spotify
- Preview songs using MusicKit JS API
- Cross-platform playlist matching
- Detailed conversion logs

### Coming Soon
- Convert Spotify playlists to Apple Music
- YouTube Music integration
- Batch playlist conversion
- Custom playlist organization

## Known Limitations

### Apple Music Integration
Currently, the app has limited access to Apple Music user libraries due to token authentication constraints. This means:

✅ **Working:**
- Converting Apple Music playlists to Spotify
- Searching Apple Music catalog
- Playing preview tracks from Apple Music

❌ **Not Yet Available:**
- Converting Spotify playlists to Apple Music (requires user library access)
- Creating playlists in user's Apple Music library

This limitation is being tracked and will be addressed in future updates.

## Technical Stack
- Django (Backend)
- JavaScript (Frontend)
- MusicKit JS API (Apple Music Integration)
- Spotify Web API (Spotify Integration)

## Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/sonusshare_v2.git
cd sonusshare_v2
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

4. Run migrations
```bash
python manage.py migrate
```

5. Start the development server
```bash
python manage.py runserver
```

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## Bug Reports

For bug reports, please include:
- Detailed description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Platform and browser information

Current known issues are tracked in the `docs/KNOWN_ISSUES.md` file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
