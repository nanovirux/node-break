import pygame
import sys
import random
import time
from collections import deque

# Initialize Pygame
pygame.init()

# Set up the display
fullscreen = True  # Set to True for fullscreen mode
if fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Full screen
else:
    screen = pygame.display.set_mode((1200, 800))  # Set a specific window size
pygame.display.set_caption("Internet City")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
BLUE = (0, 0, 255)
LIGHT_GREY = (220, 220, 220)
DARK_GREEN = (0, 150, 0)
DARK_RED = (150, 0, 0)

# City nodes and connections
node_labels = ['Google', 'YouTube', 'Fortnite', 'Minecraft', 'Roblox', 'TikTok', 'Disney+', 'Netflix',
               'Snapchat', 'Instagram', 'Twitter', 'Facebook', 'Twitch', 'Spotify', 'Hulu', 'Amazon']

# Generate positions for nodes using a grid layout to avoid overlaps and better space distribution
grid_size = 4  # Adjust grid size based on the number of nodes
space_x = screen.get_width() // (grid_size + 1)
space_y = screen.get_height() // (grid_size + 1)
positions = [(x * space_x, y * space_y) 
             for x in range(1, grid_size + 1) for y in range(1, grid_size + 1)]
random.shuffle(positions)  # Shuffle positions to randomize node placement

node_positions = {node_labels[i]: positions[i] for i in range(len(node_labels))}

# Ensure each node has at least two connections
min_connections = 2
connections = []

# First, guarantee two connections for each node
for i in range(len(node_labels)):
    connections.extend((node_positions[node_labels[i]], node_positions[node_labels[j]]) 
                       for j in random.sample([x for x in range(len(node_labels)) if x != i], min_connections))

# Now add additional connections randomly
additional_connections = [(node_positions[node_labels[i]], node_positions[node_labels[j]]) 
                          for i in range(len(node_labels)) for j in range(i + 1, len(node_labels)) if random.random() > 0.85]
connections.extend(additional_connections)

connection_status = {conn: True for conn in connections}  # True means connection is up

# Uptime and Downtime timers
uptime_start = None
total_uptime = 0
total_downtime = 0
simulation_running = False
game_duration = 26  # Duration of the game in seconds
game_start_time = None
results_screen = False  # Initialize the results screen variable

# Student name entry
student_name = ""
entering_name = True

# Font for node labels and uptime display
font = pygame.font.Font(None, 24)
large_font = pygame.font.Font(None, 36)

# Button rectangles
button_width = 100
button_height = 50
start_button = pygame.Rect(10, screen.get_height() - 60, button_width, button_height)
stop_button = pygame.Rect(120, screen.get_height() - 60, button_width, button_height)
reset_button = pygame.Rect(230, screen.get_height() - 60, button_width, button_height)
restart_button = pygame.Rect(screen.get_width() // 2 - button_width // 2, screen.get_height() - 100, button_width, button_height)  # Centered at the bottom of the results screen
exit_button = pygame.Rect(screen.get_width() - 110, 10, button_width, button_height)  # Exit button

# Animation parameters
node_max_offset = 10  # Increased node size
node_pulsate_speed = 1
last_flash_time = time.time() - 0.5  # Initialize last flash time with a delay
flash_on = False
connection_flash_speed = 0.5
connection_reestablish_speed = 0.005  # Slowed down by a factor of 10
reestablish_animations = []

# Track nodes affected by the broken connection
affected_nodes = set()

# Track the last broken connection
last_broken_connection = None

# Button animation parameters
clicked_button = None
button_click_anim_duration = 0.1  # Duration of button click animation in seconds
button_click_anim_start_time = None

# Track time since start button was clicked
time_since_start_clicked = 0

def update_time_counters():
    global total_uptime, total_downtime, uptime_start
    current_time = time.time()
    if uptime_start is not None:
        if all(connection_status.values()):
            total_uptime += current_time - uptime_start
        else:
            total_downtime += current_time - uptime_start
    uptime_start = current_time

def random_break():
    """Function to randomly select a connection to break, ensuring nodes from recent breaks are excluded."""
    global last_broken_connections, affected_nodes, recently_affected_nodes

    # Initialize last_broken_connections and recently_affected_nodes if not already done
    if 'last_broken_connections' not in globals():
        last_broken_connections = []
    if 'recently_affected_nodes' not in globals():
        recently_affected_nodes = deque(maxlen=6)  # Only keep the nodes from the last 3 breaks (2 nodes each)

    if not simulation_running or not connections:
        return

    # Filter connections to exclude those involving recently affected nodes
    available_connections = [conn for conn in connections if not (conn[0] in recently_affected_nodes or conn[1] in recently_affected_nodes)]
    if not available_connections:
        print("No available connections to break; all involve recently affected nodes.")
        return

    # Randomly choose a connection from those that are available
    broken_conn = random.choice(available_connections)
    connection_status[broken_conn] = False

    # Log the broken connection and update affected nodes
    last_broken_connections.append(broken_conn)
    if len(last_broken_connections) > 3:
        last_broken_connections.pop(0)
    
    # Update the deque of recently affected nodes
    recently_affected_nodes.extend(broken_conn)
    print(f"Breaking connection between: {broken_conn}, recently affected nodes: {list(recently_affected_nodes)}")

    # Debug output to monitor updates
    print(f"Updated list of recently affected nodes (post-update): {list(recently_affected_nodes)}")

def check_breaks():
    """Check and initiate breaks at random intervals."""
    global last_break_time
    current_time = time.time()
    if current_time - last_break_time > random.uniform(3, 7):
        random_break()
        last_break_time = current_time

def draw_button(rect, text, text_color, button_color):
    """Draw a button with text."""
    global clicked_button, button_click_anim_start_time
    mouse_pos = pygame.mouse.get_pos()
    if rect.collidepoint(mouse_pos):
        button_color = LIGHT_GREY  # Change button color when hovered
        if pygame.mouse.get_pressed()[0]:  # Check if mouse button is pressed
            clicked_button = rect
            button_click_anim_start_time = time.time()
    else:
        clicked_button = None
    
    # Animate button click
    if clicked_button == rect:
        elapsed_time = time.time() - button_click_anim_start_time
        if elapsed_time < button_click_anim_duration:
            anim_progress = elapsed_time / button_click_anim_duration
            anim_width = int(anim_progress * rect.width)
            pygame.draw.rect(screen, button_color, (rect.x, rect.y, anim_width, rect.height))
        else:
            clicked_button = None
    
    pygame.draw.rect(screen, button_color, rect)
    button_text = font.render(text, True, text_color)
    screen.blit(button_text, (rect.x + rect.width // 2 - button_text.get_width() // 2, rect.y + rect.height // 2 - button_text.get_height() // 2))

# Timing for random breaks
last_break_time = time.time()

# Main game loop
running = True
while running:
    current_time = time.time()
    if simulation_running:
        if time_since_start_clicked >= 1:  # Check if 1 second has elapsed since start button was clicked
            check_breaks()
    
    if game_start_time and current_time - game_start_time >= game_duration:
        simulation_running = False  # Stop the game after 45 seconds
        update_time_counters()  # Final update to times
        game_start_time = None  # Reset game start time for next run
        # Calculate uptime percentage
        uptime_percentage = (total_uptime / game_duration) * 100
        results_screen = True  # Activate results screen

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if exit_button.collidepoint(mouse_pos):  # Exit button functionality
                running = False
            if entering_name:
                if start_button.collidepoint(mouse_pos):  # Assuming clicking start finalizes the name entry
                    entering_name = False
                    simulation_running = True
                    game_start_time = time.time()  # Reset the game start timer
                    total_uptime = 0
                    total_downtime = 0
                    uptime_start = time.time()
                    connection_status = {conn: True for conn in connections}  # Reset connections
                    time_since_start_clicked = 0  # Reset time since start button was clicked
            elif results_screen and restart_button.collidepoint(mouse_pos):
                entering_name = True
                results_screen = False
                student_name = ""  # Reset for new game
                total_uptime = 0
                total_downtime = 0
                connection_status = {conn: True for conn in connections}  # Reset connections
            elif not entering_name:
                if start_button.collidepoint(mouse_pos) and not simulation_running:
                    simulation_running = True
                    game_start_time = time.time()  # Reset the game start timer
                    total_uptime = 0
                    total_downtime = 0
                    uptime_start = time.time()
                    connection_status = {conn: True for conn in connections}
                    time_since_start_clicked = 0  # Reset time since start button was clicked
                elif stop_button.collidepoint(mouse_pos):
                    simulation_running = False
                    update_time_counters()
                elif reset_button.collidepoint(mouse_pos):
                    # Reset the simulation and timers
                    total_uptime = 0
                    total_downtime = 0
                    uptime_start = time.time()
                    connection_status = {conn: True for conn in connections}
                    simulation_running = False
                    results_screen = False
                else:
                    # Check for connection fixes
                    for conn in connections:
                        if not connection_status[conn]:
                            node1, node2 = conn
                            if pygame.math.Vector2(mouse_pos).distance_to(node1) <= 40 or pygame.math.Vector2(mouse_pos).distance_to(node2) <= 40:
                                connection_status[conn] = True  # Fix the connection
                                affected_nodes.clear()
                                if simulation_running:
                                    update_time_counters()  # Update uptime when fixed
                                    reestablish_animations.append((node1, node2, 0))  # Start re-establishment animation

        if event.type == pygame.KEYDOWN and entering_name:
            if event.key == pygame.K_RETURN:
                entering_name = False  # End name entry on return key
            elif event.key == pygame.K_BACKSPACE:
                student_name = student_name[:-1]
            else:
                student_name += event.unicode

    screen.fill(WHITE)
    
    # Exit button
    draw_button(exit_button, "Exit", BLACK, GREY)
    
    if entering_name:
        # Name entry screen
        name_prompt = large_font.render("Enter Student Name and Press Start: ", True, BLACK)
        name_display = large_font.render(student_name, True, BLUE)
        screen.blit(name_prompt, (screen.get_width() // 2 - name_prompt.get_width() // 2, screen.get_height() // 2 - 50))
        screen.blit(name_display, (screen.get_width() // 2 - name_display.get_width() // 2, screen.get_height() // 2 + 10))
    elif results_screen:
        # Display results screen
        results_text = large_font.render(f"{student_name}'s Results", True, BLACK)
        uptime_text = large_font.render(f"Uptime: {int(total_uptime)}s", True, GREEN)
        downtime_text = large_font.render(f"Downtime: {int(total_downtime)}s", True, RED)
        percentage_text = large_font.render(f"Uptime Achieved: {uptime_percentage:.2f}%", True, BLUE)
        screen.blit(results_text, (screen.get_width() // 2 - results_text.get_width() // 2, 150))
        screen.blit(uptime_text, (screen.get_width() // 2 - uptime_text.get_width() // 2, 250))
        screen.blit(downtime_text, (screen.get_width() // 2 - downtime_text.get_width() // 2, 350))
        screen.blit(percentage_text, (screen.get_width() // 2 - percentage_text.get_width() // 2, 450))
        draw_button(restart_button, "Restart", BLACK, GREY)
    else:
        # Game screen
        draw_button(start_button, "Start", BLACK, DARK_GREEN)
        draw_button(stop_button, "Stop", BLACK, DARK_RED)
        draw_button(reset_button, "Reset", BLACK, LIGHT_GREY)
        
        # Animation: Connection flashing
        if simulation_running and current_time - last_flash_time >= connection_flash_speed:
            flash_on = not flash_on
            last_flash_time = current_time
        for connection in connections:
            if connection_status[connection]:
                color = GREEN
            else:
                color = RED if flash_on else BLACK
            pygame.draw.line(screen, color, connection[0], connection[1], 5)

        # Animation: Node pulsation and node labels
        for label, pos in node_positions.items():
            if any(conn for conn in connections if pos in conn and not connection_status[conn]):
                # If any connection to this node is broken, make it red
                node_color = RED
            else:
                node_color = GREEN
            offset = node_max_offset * (1 + random.random() * 0.2) * (1 + 0.5 * abs((current_time % node_pulsate_speed) - node_pulsate_speed / 2) / (node_pulsate_speed / 2))
            pygame.draw.circle(screen, node_color, pos, 40)  # Increased node size
            text = font.render(label, True, BLACK)
            screen.blit(text, (pos[0] - text.get_width() // 2, pos[1] - text.get_height() // 2))

        # Animation: Connection re-establishment
        for animation in reestablish_animations[:]:
            start_node, end_node, progress = animation
            if progress <= 1:
                intermediate_point = (start_node[0] + (end_node[0] - start_node[0]) * progress,
                                      start_node[1] + (end_node[1] - start_node[1]) * progress)
                pygame.draw.line(screen, RED, start_node, intermediate_point, 5)  # Draw in red
                progress += connection_reestablish_speed * (current_time - last_flash_time)
                reestablish_animations[reestablish_animations.index(animation)] = (start_node, end_node, progress)
            else:
                # Connection fully re-established, remove from animation list
                connection_status[(start_node, end_node)] = True
                reestablish_animations.remove(animation)

        # Display total uptime and downtime
        if simulation_running:
            update_time_counters()  # Continuously update timers while running
        uptime_display = font.render(f"Uptime: {int(total_uptime)}s", True, BLACK)
        downtime_display = font.render(f"Downtime: {int(total_downtime)}s", True, BLACK)
        screen.blit(uptime_display, (10, 10))
        screen.blit(downtime_display, (10, 40))
    
    pygame.display.flip()

    # Update time since start button was clicked
    if simulation_running and game_start_time is not None:
        time_since_start_clicked = current_time - game_start_time

# Quit Pygame
pygame.quit()
sys.exit()
