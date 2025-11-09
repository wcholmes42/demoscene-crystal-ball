import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image
import numpy as np
import math
import time
import os
import glob

# GLSL Fragment Shader - GPU-accelerated lens distortion
FRAGMENT_SHADER = """
#version 330 core
in vec2 fragCoord;
out vec4 fragColor;

uniform sampler2D tex;
uniform vec2 sphereCenter;
uniform float sphereRadius;
uniform float strength;
uniform vec2 resolution;

void main() {
    vec2 uv = fragCoord;
    vec2 center = sphereCenter / resolution;
    float radius = sphereRadius / resolution.x;
    
    vec2 delta = uv - center;
    float dist = length(delta);
    
    if (dist < radius) {
        float normDist = dist / radius;
        float z = sqrt(1.0 - normDist * normDist);
        float distortion = 1.0 / (1.0 + strength * (1.0 - z));
        
        vec2 distortedDelta = delta * distortion;
        vec2 sourceUV = center + distortedDelta;
        
        // Chromatic aberration
        float aberration = 0.01 * normDist;
        vec3 color;
        color.r = texture(tex, sourceUV - aberration * normalize(delta)).r;
        color.g = texture(tex, sourceUV).g;
        color.b = texture(tex, sourceUV + aberration * normalize(delta)).b;
        
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
        fragColor = texture(tex, uv);
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
    """Convert PIL image to OpenGL texture, scaled to screen"""
    # Scale image to screen size while maintaining aspect ratio
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
    
    # FULLSCREEN
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h
    
    pygame.display.set_mode((screen_width, screen_height), 
                           DOUBLEBUF | OPENGL | FULLSCREEN)
    
    # Compile shaders
    shader = compileProgram(
        compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
        compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    )
    
    # Load ALL photos from P: drive
    print("Loading photos from P: drive...")
    photo_paths = glob.glob('P:\\*.jpg') + glob.glob('P:\\*.JPG') + glob.glob('P:\\*.png')
    photo_paths = [p for p in photo_paths if os.path.isfile(p)]
    print(f"Found {len(photo_paths)} photos!")
    
    if not photo_paths:
        print("No photos found! Using fallback.")
        return
    
    # Load first photo
    current_photo_idx = 0
    current_img = Image.open(photo_paths[current_photo_idx]).convert('RGB')
    current_texture = load_texture_from_image(current_img, screen_width, screen_height)
    
    quad_vao = create_fullscreen_quad()
    glUseProgram(shader)
    
    # Get uniform locations
    loc_sphere_center = glGetUniformLocation(shader, "sphereCenter")
    loc_sphere_radius = glGetUniformLocation(shader, "sphereRadius")
    loc_strength = glGetUniformLocation(shader, "strength")
    loc_resolution = glGetUniformLocation(shader, "resolution")
    
    glUniform2f(loc_resolution, screen_width, screen_height)
    
    clock = pygame.time.Clock()
    start_time = time.time()
    photo_change_time = start_time
    running = True
    paused = False
    frame_count = 0
    
    print("DEMOSCENE SHADER RUNNING!")
    print("CONTROLS:")
    print("  ESC = Exit")
    print("  SPACE = Pause motion")
    print("  LEFT/RIGHT = Change photo manually")
    print("  Photo auto-changes every 15 seconds")
    
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    paused = not paused
                    print(f"Motion {'PAUSED' if paused else 'RESUMED'}")
                elif event.key == K_RIGHT:
                    current_photo_idx = (current_photo_idx + 1) % len(photo_paths)
                    print(f"Loading: {os.path.basename(photo_paths[current_photo_idx])}")
                    current_img = Image.open(photo_paths[current_photo_idx]).convert('RGB')
                    glDeleteTextures([current_texture])
                    current_texture = load_texture_from_image(current_img, screen_width, screen_height)
                    photo_change_time = time.time()
                elif event.key == K_LEFT:
                    current_photo_idx = (current_photo_idx - 1) % len(photo_paths)
                    print(f"Loading: {os.path.basename(photo_paths[current_photo_idx])}")
                    current_img = Image.open(photo_paths[current_photo_idx]).convert('RGB')
                    glDeleteTextures([current_texture])
                    current_texture = load_texture_from_image(current_img, screen_width, screen_height)
                    photo_change_time = time.time()
        
        # Auto-change photo every 15 seconds
        if time.time() - photo_change_time > 15.0:
            current_photo_idx = (current_photo_idx + 1) % len(photo_paths)
            print(f"Auto-loading: {os.path.basename(photo_paths[current_photo_idx])}")
            current_img = Image.open(photo_paths[current_photo_idx]).convert('RGB')
            glDeleteTextures([current_texture])
            current_texture = load_texture_from_image(current_img, screen_width, screen_height)
            photo_change_time = time.time()
        
        t = time.time() - start_time if not paused else 0
        
        # CLASSIC DEMOSCENE SINE WAVE MOTION
        center_x = screen_width/2 + math.sin(t * 1.3) * (screen_width * 0.3)
        center_x += math.cos(t * 0.8) * (screen_width * 0.15)
        
        center_y = screen_height/2 + math.cos(t * 1.6) * (screen_height * 0.25)
        center_y += math.sin(t * 1.1) * (screen_height * 0.12)
        
        # Pulsing radius
        base_radius = min(screen_width, screen_height) * 0.2
        radius = base_radius + math.sin(t * 4) * (base_radius * 0.15)
        
        # Varying distortion strength
        strength = 2.5 + math.sin(t * 2) * 0.5
        
        # Update uniforms
        glUniform2f(loc_sphere_center, center_x, center_y)
        glUniform1f(loc_sphere_radius, radius)
        glUniform1f(loc_strength, strength)
        
        # Render
        glClear(GL_COLOR_BUFFER_BIT)
        glBindTexture(GL_TEXTURE_2D, current_texture)
        glBindVertexArray(quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        pygame.display.flip()
        
        # FPS counter
        frame_count += 1
        if frame_count % 60 == 0:
            fps = frame_count / (time.time() - start_time)
            photo_name = os.path.basename(photo_paths[current_photo_idx])
            pause_text = " [PAUSED]" if paused else ""
            pygame.display.set_caption(
                f"DEMOSCENE SHADER - {fps:.0f} FPS - {photo_name}{pause_text} - ESC=Exit SPACE=Pause ARROWS=Change"
            )
        
        clock.tick(120)
    
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
