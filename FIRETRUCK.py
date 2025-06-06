import numpy as np
import tkinter as tk
from tkinter import messagebox
from queue import PriorityQueue
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# City grid: 0-road, 1-obstacle, 2-house, 3-firetruck, 4-hospital
city = np.zeros((10, 10), dtype=int)

# Obstacles
obstacle_blocks = [
    [(3, 3), (5, 3), (6, 3), (3, 4), (4, 4)],
    [(7, 1), (7, 2), (7, 4)],
    [(1, 6), (2, 6), (2, 7)],
    [(6, 7), (6, 8), (4, 6)]
]
for block in obstacle_blocks:
    for x, y in block:
        city[x, y] = 1

# Houses
houses = {
    'Shetty': (2, 2),
    'Tiwari': (2, 8),
    'Roy': (2, 5),
    'Singh': (4, 3),
    'Gupta': (5, 1),
    'Iyer': (5, 7),
    'Sharma': (6, 4),
    'Verma': (9, 3),
    'Nanda': (7, 8)
}
for pos in houses.values():
    city[pos] = 2

# Fire station and hospital
fire_station = (0, 0)
hospital = (4, 9)
city[fire_station] = 3
city[hospital] = 4

def dijkstra(grid, start, goal):
    grid = grid.copy()
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

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = current[0] + dx, current[1] + dy
            neighbor = (nx, ny)
            if 0 <= nx < 10 and 0 <= ny < 10:
                cell_value = grid[nx, ny]
                if cell_value != 1 and (cell_value != 2 or neighbor == goal):
                    new_cost = cost[current] + 1
                    if neighbor not in cost or new_cost < cost[neighbor]:
                        cost[neighbor] = new_cost
                        came_from[neighbor] = current
                        q.put((new_cost, neighbor))

    return []

class FiretruckApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Firetruck Emergency Simulation")
        self.attributes('-fullscreen', True)

        self.truck_pos = fire_station
        self.selected_house = None
        self.trail = []

        self.left_frame = tk.Frame(self)
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(self, width=200)
        self.right_frame.pack(side="right", fill="y")

        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.draw_map()

        tk.Label(self.right_frame, text="Select House Emergency:", font=("Arial", 14, "bold")).pack(pady=10)
        for house in houses.keys():
            btn = tk.Button(self.right_frame, text=house, width=15,
                            command=lambda h=house: self.handle_emergency(h))
            btn.pack(pady=5)

        tk.Button(self.right_frame, text="End Simulation", width=15,
                  command=self.end_simulation).pack(pady=20)

        self.bind("<Escape>", self.exit_fullscreen)

    def draw_map(self, trail=None):
        self.ax.clear()
        cmap = ListedColormap(['white', 'gray', 'orange', 'red', 'lightblue'])
        temp = city.copy()

        # Highlight the accident house red ONLY if an emergency is selected
        if self.selected_house:
            house_pos = houses[self.selected_house]
            temp[house_pos] = 3  # red color for accident house

        # Draw the base grid with houses, hospital, obstacles, and accident house highlight if any
        self.ax.imshow(temp, cmap=cmap)

        # Draw trail line if provided
        if trail:
            x_coords = [p[1] for p in trail]
            y_coords = [p[0] for p in trail]
            self.ax.plot(x_coords, y_coords, color='red', linewidth=2, zorder=3)

        # Write house names on the map
        for name, coord in houses.items():
            self.ax.text(coord[1], coord[0], name, color='black', fontsize=10, fontweight='bold',
                         ha='center', va='center', zorder=4)

        # Label the hospital
        self.ax.text(hospital[1], hospital[0], 'Hospital', color='black',
                     fontsize=10, fontweight='bold', ha='center', va='center', zorder=4)

        # Draw firetruck on top of everything as a red square marker
        tx, ty = self.truck_pos
        self.ax.scatter(ty, tx, s=200, c='red', marker='s', edgecolors='black', linewidth=1, zorder=5)

        # Grid lines and ticks
        self.ax.set_xticks(np.arange(-0.5, 10, 1), minor=True)
        self.ax.set_yticks(np.arange(-0.5, 10, 1), minor=True)
        self.ax.grid(which='minor', color='black', linestyle='-', linewidth=1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_title("Neighborhood Map - Firetruck Simulation", fontsize=14, fontweight='bold')

        self.canvas.draw()

    def animate_path(self, path, show_line=True):
        if show_line:
            self.trail = path
        for i, pos in enumerate(path):
            self.truck_pos = pos
            if show_line:
                self.draw_map(trail=self.trail[:i+1])
            else:
                self.draw_map()
            self.update()
            self.after(300)

    def handle_emergency(self, house_name):
        self.selected_house = house_name
        self.truck_pos = fire_station

        # Go to house
        path_to_house = dijkstra(city, self.truck_pos, houses[house_name])
        if not path_to_house:
            messagebox.showerror("Error", f"No path to {house_name}")
            return

        self.animate_path(path_to_house, show_line=True)

        injured = messagebox.askyesno("Emergency", "Is someone injured?")

        if injured:
            # Clear line to house
            self.trail = []
            self.draw_map()

            # Go to hospital
            path_to_hospital = dijkstra(city, houses[house_name], hospital)
            self.animate_path(path_to_hospital, show_line=True)

            # Clear trail after reaching hospital
            self.trail = []
            self.draw_map()

            messagebox.showinfo("Status", "Injured person transported to hospital.")

        else:
            # Show simulation complete message when "No" is clicked
            messagebox.showinfo("Simulation Complete", "Emergency simulation complete.")

        # Reset everything AFTER hospital trip or no injury
        self.truck_pos = fire_station
        self.selected_house = None  # clear selected house to revert accident house color
        self.trail = []
        self.draw_map()

    def end_simulation(self):
        self.destroy()

    def exit_fullscreen(self, event=None):
        self.attributes('-fullscreen', False)

# Start app
app = FiretruckApp()
app.mainloop()
