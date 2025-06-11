# All necessary imports
import numpy as np
import tkinter as tk
from tkinter import messagebox
from queue import PriorityQueue
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import sys

# Constants
GRID_SIZE = 30
ROAD, OBSTACLE_GREY, HOUSE, FIRETRUCK, HOSPITAL, OBSTACLE_GREEN, TREE, GARDEN = 0, 1, 2, 3, 4, 5, 6, 7

# City names (Hyderabad localities)
CITIES = ["Madhapur", "Gachibowli", "Banjara Hills", "Begumpet", "Kukatpally", "Hitech City", "Jubilee Hills"]

# Initialize city maps for each city
city_maps = {}
house_maps = {}

# Function to create a random city map
def create_random_city():
    city = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
    fire_station = (2, 2)
    hospital = (28, 28)

    for dx in range(2):
        for dy in range(2):
            city[fire_station[0]+dx, fire_station[1]+dy] = FIRETRUCK
            city[hospital[0]+dx, hospital[1]+dy] = HOSPITAL

    houses = {}
    house_positions = set()

    def can_place_block(x, y):
        if x < 0 or y < 0 or x+1 >= GRID_SIZE or y+1 >= GRID_SIZE:
            return False
        for dx in range(2):
            for dy in range(2):
                if city[x+dx, y+dy] != ROAD:
                    return False
        for px, py in house_positions.union({fire_station, hospital}):
            if abs(px - x) <= 2 and abs(py - y) <= 2:
                return False
        return True

    while len(houses) < 25:
        x, y = np.random.randint(3, GRID_SIZE - 3), np.random.randint(3, GRID_SIZE - 3)
        if can_place_block(x, y):
            name = f"House {len(houses) + 1}"
            houses[name] = (x, y)
            house_positions.add((x, y))
            for dx in range(2):
                for dy in range(2):
                    city[x+dx, y+dy] = HOUSE

    added_grey, added_green = 0, 0
    while added_grey < 90 or added_green < 30:
        x, y = np.random.randint(0, GRID_SIZE), np.random.randint(0, GRID_SIZE)
        if city[x, y] == ROAD:
            too_close = any(abs(px - x) <= 1 and abs(py - y) <= 1 for px, py in list(house_positions) + [fire_station, hospital])
            if too_close:
                continue
            if added_grey < 90:
                city[x, y] = OBSTACLE_GREY
                added_grey += 1
            elif added_green < 30:
                city[x, y] = OBSTACLE_GREEN
                added_green += 1

    return city, houses, fire_station, hospital

# Generate city maps
for name in CITIES:
    city_maps[name], house_maps[name], _, _ = create_random_city()

# Dijkstra's algorithm
def dijkstra(grid, start, goal):
    q = PriorityQueue()
    q.put((0, start))
    came_from = {}
    cost = {start: 0}
    while not q.empty():
        _, current = q.get()
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
            nx, ny = current[0] + dx, current[1] + dy
            neighbor = (nx, ny)
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                cell = grid[nx, ny]
                if cell == ROAD or neighbor == goal:
                    new_cost = cost[current] + 1
                    if neighbor not in cost or new_cost < cost[neighbor]:
                        cost[neighbor] = new_cost
                        came_from[neighbor] = current
                        q.put((new_cost, neighbor))
    return []

# Main App
class FiretruckApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Firetruck Simulation - Hyderabad Cities")
        self.geometry("1700x900")  # Wider right panel
        self.state('zoomed')
        
        self.selected_city = tk.StringVar()
        self.selected_city.set(CITIES[0])
        self.city = city_maps[CITIES[0]]
        self.houses = house_maps[CITIES[0]]
        self.fire_station = (2, 2)
        self.hospital = (28, 28)
        self.truck_pos = self.fire_station
        self.ambulance_pos = None
        self.selected_house_pos = None
        self.show_firetruck = True
        self.simulation_running = False
        self.simulation_ended = False   # <-- New flag to track if simulation ended

        self.left_frame = tk.Frame(self)
        self.left_frame.pack(side="left", fill="both", expand=True)
        self.right_frame = tk.Frame(self, width=450, bg="#f0f0f0")
        self.right_frame.pack(side="right", fill="y")

        legend_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        legend_frame.pack(pady=10, fill="x")

        legend_items = [{"color": "red", "text": "Fire Truck"},
                        {"color": "lightblue", "text": "Hospital"},
                        {"color": "grey", "text": "Obstacles"},
                        {"color": "lightgreen", "text": "Trees"},
                        {"color": "orange", "text": "Houses"}]

        for item in legend_items:
            color_label = tk.Label(legend_frame, bg=item["color"], width=2)
            color_label.pack(side="left")
            text_label = tk.Label(legend_frame, text=item["text"], bg="#f0f0f0")
            text_label.pack(side="left", padx=5)
            tk.Label(legend_frame, text="  ", bg="#f0f0f0").pack(side="left")

        self.fig, self.ax = plt.subplots(figsize=(12, 12))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        tk.Label(self.right_frame, text="Select City:", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)
        self.dropdown = tk.OptionMenu(self.right_frame, self.selected_city, *CITIES, command=self.change_city)
        self.dropdown.config(font=("Arial", 12))
        self.dropdown.pack(pady=10, fill="x", padx=20)

        # Frame for house buttons, with grid layout for 2 columns
        self.house_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        self.house_frame.pack(pady=10, fill="both", expand=True)

        self.refresh_house_buttons()
        
        # End simulation button: sets flag and closes window
        tk.Button(self.right_frame, text="End Simulation", command=self.end_simulation, bg="#d9534f", fg="white", font=("Arial", 12, "bold")).pack(pady=20, fill="x", padx=20)

        self.draw_map()

    def end_simulation(self):
        self.simulation_ended = True
        self.simulation_running = False
        self.selected_house_pos = None
        self.destroy()
        
    def change_city(self, city_name):
        if self.simulation_running:
            messagebox.showinfo("Simulation Running", "Please wait for the simulation to finish before selecting a new city.")
            return
        self.city = city_maps[city_name]
        self.houses = house_maps[city_name]
        self.truck_pos = self.fire_station
        self.ambulance_pos = None
        self.selected_house_pos = None
        self.show_firetruck = True
        for widget in self.house_frame.winfo_children():
            widget.destroy()
        self.refresh_house_buttons()
        self.draw_map()

    def refresh_house_buttons(self):
        # Clear previous buttons
        for widget in self.house_frame.winfo_children():
            widget.destroy()

        tk.Label(self.house_frame, text="Select House:", font=("Arial", 13, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=5)

        houses = list(self.houses.keys())
        for idx, house in enumerate(houses):
            row = (idx // 2) + 1  # +1 to account for label row
            col = idx % 2
            btn = tk.Button(self.house_frame, text=house, font=("Arial", 11), width=20, command=lambda h=house: self.handle_emergency(h))
            btn.grid(row=row, column=col, padx=10, pady=5, sticky="ew")

        # Make columns expand evenly
        self.house_frame.grid_columnconfigure(0, weight=1)
        self.house_frame.grid_columnconfigure(1, weight=1)

    def draw_map(self, trail=None, ambulance_trail=None):
        self.ax.clear()
        cmap = ListedColormap(['white', 'grey', 'orange', 'red', 'lightblue', 'green', 'darkgreen', 'lightgreen'])
        temp = self.city.copy()
        temp[np.isin(temp, [HOUSE, FIRETRUCK, HOSPITAL])] = ROAD
        self.ax.imshow(temp, cmap=cmap)

        for house_name, house_pos in self.houses.items():
            if house_pos == self.selected_house_pos:
                rect = patches.Rectangle((house_pos[1]-0.5, house_pos[0]-0.5), 2, 2, linewidth=2, edgecolor='black', facecolor='red', zorder=5)
            else:
                rect = patches.Rectangle((house_pos[1]-0.5, house_pos[0]-0.5), 2, 2, linewidth=1, edgecolor='black', facecolor='orange', zorder=4)
            self.ax.add_patch(rect)

        rect_station = patches.Rectangle((self.fire_station[1]-0.5, self.fire_station[0]-0.5), 2, 2, linewidth=2, edgecolor='black', facecolor='red', zorder=5)
        self.ax.add_patch(rect_station)

        rect_hosp = patches.Rectangle((self.hospital[1]-0.5, self.hospital[0]-0.5), 2, 2, linewidth=2, edgecolor='black', facecolor='lightblue', zorder=5)
        self.ax.add_patch(rect_hosp)

        if self.show_firetruck and self.truck_pos:
            tx, ty = self.truck_pos
            self.ax.scatter(ty, tx, s=300, c='red', marker='s', edgecolors='black', linewidth=1.5, zorder=6)

        if self.ambulance_pos:
            ax_, ay_ = self.ambulance_pos
            self.ax.scatter(ay_, ax_, s=300, c='lightblue', marker='s', edgecolors='black', linewidth=1.5, zorder=6)

        if trail:
            x_coords = [p[1] for p in trail]
            y_coords = [p[0] for p in trail]
            self.ax.plot(x_coords, y_coords, color='red', linewidth=2, zorder=7)

        if ambulance_trail:
            x_coords = [p[1] for p in ambulance_trail]
            y_coords = [p[0] for p in ambulance_trail]
            self.ax.plot(x_coords, y_coords, color='lightblue', linewidth=2, zorder=7)

        for name, coord in self.houses.items():
            self.ax.text(coord[1] + 0.5, coord[0] + 0.5, name, color='black', fontsize=7, ha='center', va='center', zorder=8)

        self.ax.set_xticks(np.arange(-0.5, GRID_SIZE, 1), minor=True)
        self.ax.set_yticks(np.arange(-0.5, GRID_SIZE, 1), minor=True)
        self.ax.grid(which='minor', color='black', linestyle='-', linewidth=0.7)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_title(f"Map of {self.selected_city.get()} ({GRID_SIZE}x{GRID_SIZE})", fontsize=14, fontweight='bold')
        self.canvas.draw()
    
    def animate_path(self, path, is_ambulance=False):
        for i, pos in enumerate(path):
            if self.simulation_ended:
                return  # Stop all animation if simulation ended
            if is_ambulance:
                self.ambulance_pos = pos
            else:
                self.truck_pos = pos
            self.draw_map(trail=path[:i+1] if not is_ambulance else None,
                          ambulance_trail=path[:i+1] if is_ambulance else None)
            self.update()
            self.after(50)

    def handle_emergency(self, house_name):
        if self.simulation_running or self.simulation_ended:
            return
        self.simulation_running = True
        self.simulation_ended = False
        house_pos = self.houses[house_name]
        house_entry_pos = (house_pos[0], house_pos[1])
        self.selected_house_pos = house_pos
        
        messagebox.showinfo("Emergency", f"Emergency at {house_name} in {self.selected_city.get()} at {house_pos}.")

        if self.simulation_ended:
            self.simulation_running = False
            return

         # existing code
        fs_blocks = [(self.fire_station[0]+dx, self.fire_station[1]+dy) for dx in range(2) for dy in range(2)]
        start_pos = min(fs_blocks, key=lambda b: len(dijkstra(self.city, b, house_entry_pos)) or float('inf'))
        path_to_house = dijkstra(self.city, start_pos, house_entry_pos)

        if not path_to_house:
            messagebox.showerror("Error", f"No path to {house_name}")
            self.simulation_running = False
            return

        self.show_firetruck = True
        self.animate_path(path_to_house)
        if self.simulation_ended:
            self.simulation_running = False
            return

        self.truck_pos = house_entry_pos

        if self.simulation_ended:
            self.simulation_running = False
            return

        if messagebox.askyesno("Medical Emergency", "Is this a medical emergency?"):
            hosp_blocks = [(self.hospital[0]+dx, self.hospital[1]+dy) for dx in range(2) for dy in range(2)]
            start_hosp = min(hosp_blocks, key=lambda b: len(dijkstra(self.city, b, house_entry_pos)) or float('inf'))
            path_to = dijkstra(self.city, start_hosp, house_entry_pos)
            path_back = dijkstra(self.city, house_entry_pos, start_hosp)

            if self.simulation_ended:
                self.simulation_running = False
                return
                
            messagebox.showinfo("Ambulance", f"Dispatching ambulance to {house_name} at {house_pos}.")
            hosp_blocks = [(self.hospital[0]+dx, self.hospital[1]+dy) for dx in range(2) for dy in range(2)]
            start_hosp = min(hosp_blocks, key=lambda b: len(dijkstra(self.city, b, house_pos)) or float('inf'))
            path_to = dijkstra(self.city, start_hosp, house_pos)
            path_back = dijkstra(self.city, house_pos, start_hosp)
            if path_to and path_back:
                self.show_firetruck = False
                self.ambulance_pos = start_hosp
                self.animate_path(path_to, is_ambulance=True)
                if self.simulation_ended:
                    self.simulation_running = False
                    return
                self.animate_path(path_back, is_ambulance=True)
                if self.simulation_ended:
                    self.simulation_running = False
                    return
                self.ambulance_pos = None
                messagebox.showinfo("Patient Arrived", "Patient reached hospital safely.")
                
        else:
            if self.simulation_ended:
                self.simulation_running = False
                return
            messagebox.showinfo("Handled", "Fire emergency handled.")

        if self.simulation_ended:
            self.simulation_running = False
            return

        self.truck_pos = self.fire_station
        self.show_firetruck = True
        self.draw_map()
        self.simulation_running = False
        self.selected_house_pos = None
        self.draw_map()


if __name__ == "__main__":
    app = FiretruckApp()
    app.mainloop()
