# SonusShare Frontend Implementation

## Architecture Overview

### Template Structure
```
templates/
├── base.html                # Base template with common elements
├── converter/
│   ├── index.html          # Homepage with playlist input
│   ├── review_playlist.html # Playlist review page
│   ├── about.html          # About page
│   └── contact.html        # Contact page
└── aoede_tests/            # Testing interface templates
```

## Component Design

### 1. Base Template
```html
<!-- base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SonusShare{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'converter/css/base.css' %}">
    {% block extra_styles %}{% endblock %}
</head>
<body>
    <header>
        <nav class="nav-left">
            <ul>
                <li><a href="{% url 'index' %}">Home</a></li>
                <li><a href="{% url 'about' %}">About</a></li>
            </ul>
        </nav>
        
        <div class="logo-container">
            <h1>SonusShare</h1>
        </div>
        
        <nav class="nav-right">
            <ul>
                <li><a href="{% url 'contact' %}">Contact</a></li>
                <li><a href="#">Support</a></li>
            </ul>
        </nav>
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    {% block scripts %}{% endblock %}
</body>
</html>
```

### 2. Featured Playlists Component
```html
<div class="featured-playlists">
    <h2>Featured Playlists</h2>
    <div class="playlist-grid">
        {% for playlist in featured_playlists %}
        <div class="playlist-card" onclick="convertFeaturedPlaylist('{{ playlist.url }}')">
            <div class="artwork-container" id="artwork-{{ playlist.id }}">
                <div class="playlist-artwork-placeholder">
                    <span>{{ playlist.title|slice:":1" }}</span>
                </div>
            </div>
            <div class="playlist-info">
                <div class="playlist-title">{{ playlist.title }}</div>
                <div class="playlist-curator">{{ playlist.curator }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

## Styling Architecture

### 1. Base Styles
```css
/* base.css */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #fff;
}

/* Header Navigation */
header {
    position: relative;
    padding: 2rem 4rem;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
```

### 2. Component-Specific Styles
```css
/* Featured Playlists */
.playlist-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
}

.playlist-card {
    background: white;
    border: 2px solid #333;
    border-radius: 8px;
    overflow: hidden;
    transition: transform 0.3s ease;
}

/* Artwork Container */
.artwork-container {
    position: relative;
    width: 100%;
    aspect-ratio: 1;
    background: #f5f5f5;
    overflow: hidden;
}
```

## JavaScript Implementation

### 1. MusicKit Integration
```javascript
document.addEventListener('musickitloaded', async function() {
    try {
        const music = await MusicKit.configure({
            developerToken: token,
            app: {
                name: 'SonusShare',
                build: '1.0.0'
            }
        });
        
        // Initialize features that require MusicKit
        initializePlaylistArtwork();
        initializePlayback();
    } catch (error) {
        console.error('Failed to initialize MusicKit:', error);
        showError('Failed to initialize Apple Music integration');
    }
});
```

### 2. Dynamic Artwork Loading
```javascript
async function loadPlaylistArtwork(playlist) {
    try {
        const response = await fetch(
            `https://api.music.apple.com/v1/catalog/gb/playlists/${playlist.id}`,
            {
                headers: {
                    'Authorization': `Bearer ${developerToken}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        const data = await response.json();
        if (data.data[0].attributes.artwork) {
            const artwork = data.data[0].attributes.artwork;
            const artworkUrl = artwork.url
                .replace('{w}', '600')
                .replace('{h}', '600');
                
            updateArtwork(playlist.id, artworkUrl);
        }
    } catch (error) {
        console.error('Failed to load artwork:', error);
    }
}
```

## User Interface Components

### 1. Loading States
```css
.loading {
    position: relative;
    pointer-events: none;
}

.loading::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
}

.spinner {
    width: 30px;
    height: 30px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #333;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
```

### 2. Error Handling
```javascript
function showError(message) {
    const errorContainer = document.createElement('div');
    errorContainer.className = 'error-message';
    errorContainer.textContent = message;
    
    const container = document.querySelector('.featured-playlists');
    container.insertBefore(errorContainer, container.firstChild);
    
    setTimeout(() => {
        errorContainer.remove();
    }, 5000);
}
```

## Responsive Design

### 1. Breakpoint System
```css
/* Mobile First Approach */
.playlist-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
    padding: 1rem;
}

/* Tablet */
@media screen and (min-width: 768px) {
    .playlist-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
        padding: 1.5rem;
    }
}

/* Desktop */
@media screen and (min-width: 1024px) {
    .playlist-grid {
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        padding: 2rem;
    }
}
```

### 2. Responsive Images
```css
.playlist-artwork {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
}

/* High DPI Screens */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
    .playlist-artwork {
        image-rendering: -webkit-optimize-contrast;
    }
}
```

## Performance Optimizations

### 1. Image Loading
```html
<img src="{{ artwork_url }}"
     alt="{{ playlist.title }}"
     class="playlist-artwork"
     loading="lazy"
     decoding="async"
     srcset="{{ artwork_url_300 }} 300w,
             {{ artwork_url_600 }} 600w,
             {{ artwork_url_1200 }} 1200w"
     sizes="(max-width: 768px) 100vw,
            (max-width: 1024px) 50vw,
            33vw">
```

### 2. Resource Hints
```html
<head>
    <!-- Preconnect to API domains -->
    <link rel="preconnect" href="https://api.music.apple.com">
    <link rel="preconnect" href="https://api.spotify.com">
    
    <!-- Preload critical resources -->
    <link rel="preload" href="{% static 'converter/css/base.css' %}" as="style">
    <link rel="preload" href="https://js-cdn.music.apple.com/musickit/v3/musickit.js" as="script">
</head>
```

## Accessibility

### 1. ARIA Attributes
```html
<div class="playlist-card" 
     role="button"
     aria-label="Convert playlist: {{ playlist.title }}"
     tabindex="0"
     onclick="convertFeaturedPlaylist('{{ playlist.url }}')">
    <!-- Content -->
</div>
```

### 2. Keyboard Navigation
```javascript
function initializeKeyboardNavigation() {
    const cards = document.querySelectorAll('.playlist-card');
    
    cards.forEach(card => {
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });
}
```

## Testing

### 1. Component Tests
```javascript
describe('Featured Playlists', () => {
    test('loads artwork successfully', async () => {
        const playlist = {
            id: 'test-id',
            title: 'Test Playlist'
        };
        
        await loadPlaylistArtwork(playlist);
        
        const artwork = document.querySelector(`#artwork-${playlist.id} img`);
        expect(artwork).toBeTruthy();
        expect(artwork.src).toContain('600x600');
    });
});
```

### 2. Integration Tests
```javascript
describe('Playlist Conversion', () => {
    test('converts playlist successfully', async () => {
        const playlistUrl = 'https://music.apple.com/playlist/test';
        await convertFeaturedPlaylist(playlistUrl);
        
        // Check redirect
        expect(window.location.href).toContain('/convert_playlist');
    });
});
