# 🔮 DEMOSCENE CRYSTAL BALL 💾

**A lifelong dream realized: GPU-accelerated spherical lens distortion with real-time animation**

## What Is This?

This is pure 90s demoscene aesthetic brought to life with modern GPU shaders. A floating crystal ball with physically-accurate lens distortion bounces around your photos in classic Lissajous sine wave patterns.

Built with raw OpenGL fragment shaders, not some hand-wavy filter library. Real physics, real chromatic aberration, real specular highlights.

## Features

- **GPU Fragment Shader**: GLSL-based spherical lens distortion running at 120 FPS
- **Chromatic Aberration**: RGB channels split like real glass prisms
- **Classic Demoscene Motion**: Multiple sine wave frequencies combined (Lissajous curves)
- **Auto Photo Cycling**: Loads all images from P: drive, changes every 15 seconds
- **Manual Controls**: Arrow keys to browse, space to pause
- **Pulsing Effects**: Radius and distortion strength modulate over time
- **Fullscreen Glory**: Proper demoscene presentation

## The Physics

The shader implements real spherical lens optics:
- Inverse radial mapping for magnification
- z = √(1 - r²) models actual sphere surface geometry
- Distortion = 1/(1 + strength × (1-z)) simulates light refraction
- Chromatic aberration offsets R/G/B channels based on distance from center
- Specular highlights and ambient occlusion for 3D depth

## Requirements

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate Pillow numpy
```

## Usage

```bash
python crystal_ball_demo.py
```

**Controls:**
- `ESC` - Exit
- `SPACE` - Pause/Resume motion
- `LEFT/RIGHT` - Manually change photos
- Photos auto-cycle every 15 seconds

## Configuration

Edit the photo path in line 88:
```python
photo_paths = glob.glob('P:\\*.jpg') + glob.glob('P:\\*.JPG')
```

Change to your photo directory. The demo will load all images and cycle through them.

## Why This Exists

Because 12-year-old me dreamed of making demoscene graphics, and today that dream came true.

This is what happens when you give Claude Desktop Commander access and say "make it like the old demo scene."

## Technical Details

- **Language**: Python 3.11+
- **Graphics**: OpenGL 3.3 Core Profile
- **Shaders**: GLSL 330
- **Target FPS**: 120 (GPU-accelerated, we can!)

## Screenshot

*(Your photos distorted through a floating crystal ball with chromatic aberration and specular highlights)*

## License

MIT - Do whatever you want with it. Make demos. Live the dream.

## Credits

Built in one glorious session on January 15, 2025.  
12-year-old Bill is squealing with joy. 💾🌈✨

---

*"It's not just code. It's a childhood dream realized."*
