import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image, ImageOps
import numpy as np
import math
import time
import os
import glob

# GLSL Fragment Shader - GPU-accelerated lens distortion with DISSOLVE effect
FRAGMENT_SHADER = """
#version 330 core
in vec2 fragCoord;
out vec4 fragColor;

uniform sampler2D tex1;
uniform sampler2D tex2;
uniform float crossfade;
uniform vec2 sphereCenter;
uniform float sphereRadius;
uniform float strength;
uniform vec2 resolution;

// Random noise function for dissolve pattern
float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

void main() {
    vec2 uv = fragCoord;
    vec2 center = sphereCenter / resolution;
    float radius = sphereRadius / resolution.x;
    
    vec2 delta = uv - center;
    float dist = length(delta);
    
    // Generate dissolve pattern (organic random noise)
    float dissolveNoise = random(uv * 500.0);  // Higher frequency for finer pattern
    
    // Smooth dissolve with wider soft edges for organic look
    float dissolveEdge = 0.15;  // Wider soft edge for smoother transition
    float dissolveMix = smoothstep(crossfade - dissolveEdge, crossfade + dissolveEdge, dissolveNoise);
    
    // Sample both textures with dissolve effect
    vec3 color1 = texture(tex1, uv).rgb;
    vec3 color2 = texture(tex2, uv).rgb;
    vec3 baseColor = mix(color1, color2, dissolveMix);
    
    if (dist < radius) {
        float normDist = dist / radius;
        float z = sqrt(1.0 - normDist * normDist);
        float distortion = 1.0 / (1.0 + strength * (1.0 - z));
        
        vec2 distortedDelta = delta * distortion;
        vec2 sourceUV = center + distortedDelta;
        
        // Chromatic aberration on both textures with dissolve
        float aberration = 0.01 * normDist;
        vec3 color1_distorted, color2_distorted;
        
        color1_distorted.r = texture(tex1, sourceUV - aberration * normalize(delta)).r;
        color1_distorted.g = texture(tex1, sourceUV).g;
        color1_distorted.b = texture(tex1, sourceUV + aberration * normalize(delta)).b;
        
        color2_distorted.r = texture(tex2, sourceUV - aberration * normalize(delta)).r;
        color2_distorted.g = texture(tex2, sourceUV).g;
        color2_distorted.b = texture(tex2, sourceUV + aberration * normalize(delta)).b;
        
        // Apply dissolve pattern to distorted colors
        float dissolveNoise_sphere = random(sourceUV * 100.0);
        float dissolveThreshold_sphere = crossfade + (dissolveNoise_sphere - 0.5) * 0.1;
        float dissolveMix_sphere = smoothstep(dissolveThreshold_sphere - 0.1, dissolveThreshold_sphere + 0.1, dissolveNoise_sphere);
        
        vec3 color = mix(color1_distorted, color2_distorted, dissolveMix_sphere);
        
        // Specular highlight
        vec2 highlightPos = center + vec2(-0.3, -0.3) * radius;
        float highlightDist = length(uv - highlightPos);
        if (highlightDist < radius * 0.3) {
            float intensity = pow(1.0 - highlightDist / (radius * 0.3), 2.0);
            color += vec3(intensity * 0.5);
        }
        
        // Edge darkening
        float edgeDarken = 1.0 - 0.4 * pow(normDist, 2.0);
        color *= edgeDarken;
        
        fragColor = vec4(color, 1.0);
    } else {
        fragColor = vec4(baseColor, 1.0);
    }
}
"""

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texCoord;
out vec2 fragCoord;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    fragCoord = texCoord;
}
"""

def load_texture_from_image(img, screen_width, screen_height):
    """Convert PIL image to OpenGL texture, scaled to screen with proper orientation"""
    # CRITICAL: Apply EXIF orientation to fix upside-down/rotated photos
    img = ImageOps.exif_transpose(img)
    
    img_ratio = img.width / img.height
    screen_ratio = screen_width / screen_height
    
    if img_ratio > screen_ratio:
        new_width = screen_width
        new_height = int(screen_width / img_ratio)
    else:
        new_height = screen_height
        new_width = int(screen_height * img_ratio)
    
    img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Center on black background
    bg = Image.new('RGB', (screen_width, screen_height), (0, 0, 0))
    offset = ((screen_width - new_width) // 2, (screen_height - new_height) // 2)
    bg.paste(img, offset)
    
    img = bg.transpose(Image.FLIP_TOP_BOTTOM)
    img_data = np.array(img, dtype=np.uint8)
    
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, screen_width, screen_height,
                 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return texture

def create_fullscreen_quad():
    """Create fullscreen quad"""
    vertices = np.array([
        -1.0, -1.0,  0.0, 0.0,
         1.0, -1.0,  1.0, 0.0,
         1.0,  1.0,  1.0, 1.0,
        -1.0, -1.0,  0.0, 0.0,
         1.0,  1.0,  1.0, 1.0,
        -1.0,  1.0,  0.0, 1.0
    ], dtype=np.float32)
    
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
    
    glBindVertexArray(0)
    return vao

def main():
    pygame.init()
    
    # Initialize font for on-screen text
    pygame.font.init()
    
    # FULLSCREEN with VSYNC for smooth display
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h
    
    # Enable VSYNC (swap_control)
    pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
    
    pygame.display.set_mode((screen_width, screen_height), 
                           DOUBLEBUF | OPENGL | FULLSCREEN)
    pygame.display.set_caption("DEMOSCENE CRYSTAL BALL")
    
    # Compile shaders
    shader = compileProgram(
        compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
        compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    )
    
    # Load ALL photos from P: drive and SORT them
    print("Loading photos from P: drive...")
    photo_paths = glob.glob('P:\\*.jpg') + glob.glob('P:\\*.JPG') + glob.glob('P:\\*.png')
    photo_paths = [p for p in photo_paths if os.path.isfile(p)]
    photo_paths.sort()  # Sort alphabetically by filename
    print(f"Found {len(photo_paths)} photos (sorted by filename)")
    print(f"First: {os.path.basename(photo_paths[0])}")
    print(f"Last: {os.path.basename(photo_paths[-1])}")
    
    if not photo_paths:
        print("No photos found!")
        return
    
    # Load first two photos for cross-fade
    current_photo_idx = 0
    next_photo_idx = 1
    
    current_img = Image.open(photo_paths[current_photo_idx]).convert('RGB')
    next_img = Image.open(photo_paths[next_photo_idx]).convert('RGB')
    
    texture1 = load_texture_from_image(current_img, screen_width, screen_height)
    texture2 = load_texture_from_image(next_img, screen_width, screen_height)
    
    quad_vao = create_fullscreen_quad()
    glUseProgram(shader)
    
    # Get uniform locations
    loc_tex1 = glGetUniformLocation(shader, "tex1")
    loc_tex2 = glGetUniformLocation(shader, "tex2")
    loc_crossfade = glGetUniformLocation(shader, "crossfade")
    loc_sphere_center = glGetUniformLocation(shader, "sphereCenter")
    loc_sphere_radius = glGetUniformLocation(shader, "sphereRadius")
    loc_strength = glGetUniformLocation(shader, "strength")
    loc_resolution = glGetUniformLocation(shader, "resolution")
    
    glUniform2f(loc_resolution, screen_width, screen_height)
    glUniform1i(loc_tex1, 0)  # Texture unit 0
    glUniform1i(loc_tex2, 1)  # Texture unit 1
    
    clock = pygame.time.Clock()
    start_time = time.time()
    photo_change_time = start_time
    crossfade_start = start_time
    crossfade_duration = 8.0  # 8 SECOND slow dissolve
    photo_display_time = 30.0  # 30 SECONDS per photo
    running = True
    paused = False
    frame_count = 0
    
    print("DEMOSCENE SHADER RUNNING!")
    print("CONTROLS:")
    print("  ESC = Exit")
    print("  SPACE = Pause motion")
    print("  LEFT/RIGHT = Change photo manually")
    print("  Photos display for 30 seconds with 8-second smooth dissolve")
    
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    paused = not paused
                elif event.key == K_RIGHT or event.key == K_LEFT:
                    # Manual photo change with cross-fade
                    if event.key == K_RIGHT:
                        next_photo_idx = (current_photo_idx + 1) % len(photo_paths)
                    else:
                        next_photo_idx = (current_photo_idx - 1) % len(photo_paths)
                    
                    print(f"Loading: {os.path.basename(photo_paths[next_photo_idx])}")
                    next_img = Image.open(photo_paths[next_photo_idx]).convert('RGB')
                    glDeleteTextures([texture2])
                    texture2 = load_texture_from_image(next_img, screen_width, screen_height)
                    crossfade_start = time.time()
                    photo_change_time = time.time()
        
        current_time = time.time()
        t = current_time - start_time if not paused else 0
        
        # Show countdown every 5 seconds
        time_on_photo = current_time - photo_change_time
        if int(time_on_photo) % 5 == 0 and int(time_on_photo * 10) % 50 == 0:  # Once per 5 sec
            remaining = int(photo_display_time - time_on_photo)
            print(f"[Photo #{current_photo_idx + 1}] {remaining}s until next photo...")
        
        # Auto-change photo with cross-fade every 30 seconds
        if current_time - photo_change_time > photo_display_time:
            next_photo_idx = (current_photo_idx + 1) % len(photo_paths)
            print("\n" + "="*60)
            print(f"[{int(current_time - start_time)}s] PHOTO CHANGE #{next_photo_idx + 1}/{len(photo_paths)}")
            print(f"Cross-fading to: {os.path.basename(photo_paths[next_photo_idx])}")
            print("="*60 + "\n")
            next_img = Image.open(photo_paths[next_photo_idx]).convert('RGB')
            glDeleteTextures([texture2])
            texture2 = load_texture_from_image(next_img, screen_width, screen_height)
            crossfade_start = current_time
            photo_change_time = current_time
        
        # Calculate cross-fade amount (0.0 = texture1, 1.0 = texture2)
        crossfade_progress = min(1.0, (current_time - crossfade_start) / crossfade_duration)
        
        # When cross-fade complete, swap textures and PRE-LOAD next
        if crossfade_progress >= 1.0 and current_photo_idx != next_photo_idx:
            print(f"[CROSSFADE COMPLETE] Swapping to photo #{next_photo_idx + 1}")
            glDeleteTextures([texture1])
            texture1 = texture2
            current_photo_idx = next_photo_idx
            
            # PRE-LOAD next photo into texture2 so OLD and NEW are always ready
            next_photo_idx = (current_photo_idx + 1) % len(photo_paths)
            print(f"[PRE-LOAD] Loading photo #{next_photo_idx + 1} for next transition")
            next_img = Image.open(photo_paths[next_photo_idx]).convert('RGB')
            texture2 = load_texture_from_image(next_img, screen_width, screen_height)
            
            # Reset crossfade to prevent re-triggering
            crossfade_start = current_time - crossfade_duration  # Keep at 1.0
        
        # IMPROVED DEMOSCENE MOTION - More complex Lissajous with rotation
        # Multiple sine waves with different frequencies and phases
        center_x = screen_width/2 + math.sin(t * 0.8) * (screen_width * 0.3)
        center_x += math.cos(t * 1.3) * (screen_width * 0.15)
        center_x += math.sin(t * 2.1) * (screen_width * 0.05)  # Extra detail
        
        center_y = screen_height/2 + math.cos(t * 1.2) * (screen_height * 0.25)
        center_y += math.sin(t * 0.9) * (screen_height * 0.12)
        center_y += math.cos(t * 1.7) * (screen_height * 0.08)  # Extra detail
        
        # Pulsing radius with multiple frequencies
        base_radius = min(screen_width, screen_height) * 0.18
        radius = base_radius + math.sin(t * 3.2) * (base_radius * 0.12)
        radius += math.cos(t * 5.1) * (base_radius * 0.05)  # Extra pulse
        
        # Varying distortion strength (breathing effect)
        strength = 2.3 + math.sin(t * 1.8) * 0.4
        strength += math.cos(t * 3.5) * 0.2  # Extra variation
        
        # Update shader uniforms
        glUniform1f(loc_crossfade, crossfade_progress)
        glUniform2f(loc_sphere_center, center_x, center_y)
        glUniform1f(loc_sphere_radius, radius)
        glUniform1f(loc_strength, strength)
        
        # Render with both textures
        glClear(GL_COLOR_BUFFER_BIT)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture1)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, texture2)
        
        glBindVertexArray(quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        pygame.display.flip()
        
        # FPS counter with timing info
        frame_count += 1
        if frame_count % 60 == 0:
            fps = frame_count / (time.time() - start_time)
            photo_name = os.path.basename(photo_paths[current_photo_idx])
            pause_text = " [PAUSED]" if paused else ""
            fade_pct = int(crossfade_progress * 100)
            time_on_photo = int(current_time - photo_change_time)
            time_remaining = int(photo_display_time - (current_time - photo_change_time))
            pygame.display.set_caption(
                f"DEMOSCENE - {fps:.0f} FPS - {photo_name} ({time_remaining}s left, fade:{fade_pct}%){pause_text}"
            )
        
        clock.tick(60)  # 60 FPS with VSYNC
    
    pygame.quit()
    print("Demo closed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
