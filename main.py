import pygame
import random
import os
from dataclasses import dataclass

@dataclass
class GlitchStrip:
    x: int          # x position within image
    y: int          # y position within image
    width: int      # width of the glitch
    height: int     # height of the glitch
    offset_x: int   # current x offset
    offset_y: int   # current y offset

# Initialize Pygame and set a temporary display mode
pygame.init()
temp_surface = pygame.display.set_mode((800, 600))  # Temporary surface for image loading

# Load image first
if not os.path.exists("image.png"):
    # Create a default surface if image doesn't exist
    original_image = pygame.Surface((200, 200), pygame.SRCALPHA)
    original_image.fill((0, 0, 0, 0))
    pygame.draw.circle(original_image, (255, 255, 255, 255), (100, 100), 80)
else:
    original_image = pygame.image.load("image.png").convert_alpha()

# Constants
PADDING = 100  # Padding around the image
WINDOW_WIDTH = original_image.get_width() + PADDING * 2
WINDOW_HEIGHT = original_image.get_height() + PADDING * 2
GLITCH_MAX_OFFSET = 50
MIN_STRIP_HEIGHT = 10
MAX_STRIP_HEIGHT = 40
MIN_STRIP_WIDTH = 50
MAX_NUM_GLITCHES = 20
MIN_NUM_GLITCHES = 1
CHECKER_SIZE = 10

# Colors
GLITCH_BLUE = (0, 140, 255)  # Lighter, more fluorescent blue
GLITCH_RED = (255, 0, 0)

# Set up display with proper size
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Glitch Effect")

# Create checkerboard pattern
checker_surface = pygame.Surface((CHECKER_SIZE * 2, CHECKER_SIZE * 2))
pygame.draw.rect(checker_surface, (128, 128, 128), (0, 0, CHECKER_SIZE, CHECKER_SIZE))
pygame.draw.rect(checker_surface, (64, 64, 64), (CHECKER_SIZE, 0, CHECKER_SIZE, CHECKER_SIZE))
pygame.draw.rect(checker_surface, (64, 64, 64), (0, CHECKER_SIZE, CHECKER_SIZE, CHECKER_SIZE))
pygame.draw.rect(checker_surface, (128, 128, 128), (CHECKER_SIZE, CHECKER_SIZE, CHECKER_SIZE, CHECKER_SIZE))

# Create working copies
base_image = original_image.copy()
red_image = pygame.Surface(original_image.get_size(), pygame.SRCALPHA)
blue_image = pygame.Surface(original_image.get_size(), pygame.SRCALPHA)
overlap_map = pygame.Surface(original_image.get_size(), pygame.SRCALPHA)

# Initial positions
image_x = PADDING
image_y = PADDING
pan_offset_x = 0
pan_offset_y = 0
panning = False
pan_start_pos = None

# Glitch parameters
glitch_direction_x = 1
glitch_direction_y = 0
glitch_intensity = 0
num_glitches = 3  # Start with 3 glitches
paused = False
active_glitches: list[GlitchStrip] = []

# Mouse handling variables
dragging = False
drag_start = None
drag_end = None

def create_glitch_strip() -> GlitchStrip:
    height = random.randint(MIN_STRIP_HEIGHT, MAX_STRIP_HEIGHT)
    width = random.randint(MIN_STRIP_WIDTH, original_image.get_width())
    x = random.randint(0, original_image.get_width() - width)
    y = random.randint(0, original_image.get_height() - height)
    
    return GlitchStrip(
        x=x,
        y=y,
        width=width,
        height=height,
        offset_x=0,
        offset_y=0
    )

def update_glitches():
    global active_glitches
    
    # Ensure we have the correct number of glitches
    while len(active_glitches) < num_glitches:
        active_glitches.append(create_glitch_strip())
    while len(active_glitches) > num_glitches:
        active_glitches.pop()
    
    # Update offsets for each glitch
    for glitch in active_glitches:
        glitch.offset_x = random.randint(-int(glitch_intensity), int(glitch_intensity)) * glitch_direction_x
        glitch.offset_y = random.randint(-int(glitch_intensity * 0.2), int(glitch_intensity * 0.2)) * glitch_direction_y

def apply_glitch_effect():
    # Reset images
    red_image.fill((0, 0, 0, 0))
    blue_image.fill((0, 0, 0, 0))
    overlap_map.fill((0, 0, 0, 0))
    
    # Track which pixels are affected by glitches
    affected_pixels = set()
    
    # First pass: Apply red glitches and track affected pixels
    for glitch in active_glitches:
        strip_rect = pygame.Rect(glitch.x, glitch.y, glitch.width, glitch.height)
        
        for x in range(strip_rect.left, strip_rect.right):
            for y in range(strip_rect.top, strip_rect.bottom):
                if 0 <= x < original_image.get_width() and 0 <= y < original_image.get_height():
                    color = original_image.get_at((x, y))
                    if color.a > 0:  # If pixel is not fully transparent
                        pixel_key = (x, y)
                        affected_pixels.add(pixel_key)
                        
                        # Red version (static)
                        red_image.set_at((x, y), (GLITCH_RED[0], GLITCH_RED[1], GLITCH_RED[2], color.a))
                        
                        # Track original color for potential overlap
                        overlap_map.set_at((x, y), color)
    
    # Second pass: Apply blue glitches and handle overlaps
    for glitch in active_glitches:
        strip_rect = pygame.Rect(glitch.x, glitch.y, glitch.width, glitch.height)
        
        for x in range(strip_rect.left, strip_rect.right):
            for y in range(strip_rect.top, strip_rect.bottom):
                if 0 <= x < original_image.get_width() and 0 <= y < original_image.get_height():
                    color = original_image.get_at((x, y))
                    if color.a > 0:  # If pixel is not fully transparent
                        pixel_key = (x + glitch.offset_x, y + glitch.offset_y)
                        
                        # Blue version (moving) - only blue if not overlapping with original
                        dest_x = x + glitch.offset_x
                        dest_y = y + glitch.offset_y
                        if (0 <= dest_x < original_image.get_width() and 
                            0 <= dest_y < original_image.get_height()):
                            orig_color = original_image.get_at((int(dest_x), int(dest_y)))
                            if orig_color.a == 0:  # Only blue if not overlapping with original
                                blue_image.set_at((x, y), (GLITCH_BLUE[0], GLITCH_BLUE[1], GLITCH_BLUE[2], color.a))
                            else:
                                blue_image.set_at((x, y), orig_color)

def save_glitched_image():
    # Create a surface for the final image
    final_surface = pygame.Surface(original_image.get_size(), pygame.SRCALPHA)
    
    # Draw the base image
    final_surface.blit(base_image, (0, 0))
    
    # Draw the red glitches
    final_surface.blit(red_image, (0, 0))
    
    # Draw the blue glitches with offsets
    for glitch in active_glitches:
        glitch_surface = pygame.Surface((glitch.width, glitch.height), pygame.SRCALPHA)
        glitch_surface.blit(blue_image, (-glitch.x, -glitch.y))
        final_surface.blit(glitch_surface, (glitch.x + glitch.offset_x, glitch.y + glitch.offset_y))
    
    # Save the surface
    pygame.image.save(final_surface, "glitched_output.png")

running = True
clock = pygame.time.Clock()
frame_count = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RETURN:
                save_glitched_image()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                dragging = True
                drag_start = event.pos
            elif event.button == 2:  # Middle mouse button
                panning = True
                pan_start_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging:
                drag_end = event.pos
                dragging = False
                
                # Calculate direction and intensity from drag
                if drag_start and drag_end:
                    dx = drag_end[0] - drag_start[0]
                    dy = drag_end[1] - drag_start[1]
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    
                    # Normalize direction
                    if distance > 0:
                        glitch_direction_x = dx / distance
                        glitch_direction_y = dy / distance
                        glitch_intensity = min(distance / 5, GLITCH_MAX_OFFSET)
            elif event.button == 2:  # Middle mouse button
                panning = False
        elif event.type == pygame.MOUSEMOTION:
            if panning and pan_start_pos:
                dx = event.pos[0] - pan_start_pos[0]
                dy = event.pos[1] - pan_start_pos[1]
                pan_offset_x += dx
                pan_offset_y += dy
                pan_start_pos = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            # Adjust number of glitches with mouse wheel
            num_glitches = max(MIN_NUM_GLITCHES, min(MAX_NUM_GLITCHES, num_glitches + event.y))
    
    if not paused:
        # Update glitch positions periodically
        frame_count += 1
        if frame_count % 30 == 0:  # Change every 30 frames
            # Recreate some random glitches
            num_to_update = random.randint(1, max(1, num_glitches // 2))
            for _ in range(num_to_update):
                if active_glitches:
                    idx = random.randint(0, len(active_glitches) - 1)
                    active_glitches[idx] = create_glitch_strip()
        
        # Apply glitch effect
        if glitch_intensity > 0:
            update_glitches()
            apply_glitch_effect()
    
    # Draw checkerboard background
    for y in range(0, WINDOW_HEIGHT, CHECKER_SIZE * 2):
        for x in range(0, WINDOW_WIDTH, CHECKER_SIZE * 2):
            screen.blit(checker_surface, (x, y))
    
    # Calculate final drawing position with pan offset
    final_x = image_x + pan_offset_x
    final_y = image_y + pan_offset_y
    
    # Draw
    screen.blit(base_image, (final_x, final_y))  # Draw original image
    screen.blit(red_image, (final_x, final_y))   # Draw red strips (static)
    
    # Draw each blue glitch with its offset
    for glitch in active_glitches:
        glitch_surface = pygame.Surface((glitch.width, glitch.height), pygame.SRCALPHA)
        glitch_surface.blit(blue_image, (-glitch.x, -glitch.y))
        screen.blit(glitch_surface, (
            final_x + glitch.x + glitch.offset_x,
            final_y + glitch.y + glitch.offset_y
        ))
    
    # Draw drag line while dragging
    if dragging and drag_start:
        pygame.draw.line(screen, (255, 255, 255), drag_start, pygame.mouse.get_pos())
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
