import pygame
import mysql.connector
import time
from datetime import datetime
from config import DB_CONFIG

REFRESH_RATE = 1.0 
DISPLAY_DURATION = 8 

COLOR_BG = (30, 30, 30)
COLOR_ACCENT = (0, 255, 127)
COLOR_TEXT_MAIN = (255, 255, 255)
COLOR_TEXT_SEC = (200, 200, 200)

def get_latest_checkin():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        
        sql = """
            SELECT e.name, e.post, a.check_in 
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.date = CURDATE()
            ORDER BY a.check_in DESC 
            LIMIT 1
        """
        cur.execute(sql)
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        return row
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def get_dummy_schedule(post):
    if "Manager" in post:
        return ["10:00 AM - Strategy Sync", "02:00 PM - Client Call", "04:30 PM - HR Review"]
    elif "Dev" in post:
        return ["09:30 AM - Standup", "11:00 AM - Code Review", "03:00 PM - Deployment"]
    else:
        return ["09:00 AM - Check Emails", "01:00 PM - Lunch Break", "05:00 PM - Daily Report"]

def draw_text(surface, text, size, x, y, color=COLOR_TEXT_MAIN, center=True):
    font = pygame.font.SysFont("Arial", size, bold=True)
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(text_surface, rect)

def main():
    pygame.init()
    
    screen = pygame.display.set_mode((800, 600))
    W, H = screen.get_size()
    pygame.display.set_caption("FaceSched AI - Dashboard")

    running = True
    clock = pygame.time.Clock()
    
    last_db_check = 0
    current_view = "IDLE" 
    
    display_data = {}
    display_start_time = 0
    
    last_processed_timestamp = None 

    print("Display Module Started... Waiting for check-ins.")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        now = time.time()
        
        if now - last_db_check > REFRESH_RATE:
            last_db_check = now
            record = get_latest_checkin()
            
            if record:
                check_in_time_str = str(record['check_in'])
                
                if check_in_time_str != last_processed_timestamp:
                    print(f"New Check-in: {record['name']} at {check_in_time_str}")
                    
                    last_processed_timestamp = check_in_time_str
                    
                    display_data = {
                        "name": record['name'],
                        "post": record['post'],
                        "tasks": get_dummy_schedule(record['post']),
                        "time": check_in_time_str
                    }
                    current_view = "WELCOME"
                    display_start_time = now

        if current_view == "WELCOME":
            if now - display_start_time > DISPLAY_DURATION:
                current_view = "IDLE"

        screen.fill(COLOR_BG)
        
        if current_view == "IDLE":
            draw_text(screen, "FaceSched AI", 60, W//2, H//2 - 40, COLOR_ACCENT)
            draw_text(screen, "Ready for Check-in...", 30, W//2, H//2 + 40, COLOR_TEXT_SEC)
            
            curr_time_str = datetime.now().strftime("%I:%M:%S %p")
            draw_text(screen, curr_time_str, 25, W - 100, H - 40, (100, 100, 100))

        elif current_view == "WELCOME":
            emp_name = display_data.get('name', 'Employee')
            emp_post = display_data.get('post', 'Staff')
            emp_tasks = display_data.get('tasks', [])
            
            draw_text(screen, f"Welcome, {emp_name}!", 50, W//2, H//4, COLOR_ACCENT)
            draw_text(screen, emp_post, 30, W//2, H//4 + 50, COLOR_TEXT_SEC)
            
            box_y = H//2
            draw_text(screen, "Today's Schedule:", 30, W//2, box_y - 30, COLOR_TEXT_MAIN)
            
            for i, task in enumerate(emp_tasks):
                draw_text(screen, f"• {task}", 24, W//2, box_y + 20 + (i*35), COLOR_TEXT_SEC)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()