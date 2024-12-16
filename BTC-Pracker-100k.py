import tkinter as tk
from tkinter import simpledialog
import requests
import winreg
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import numpy as np
import ctypes
import matplotlib.dates as mdates
import sys
from tkinter import Text, Toplevel, Checkbutton, IntVar


WINDOW_POSITION_FILE = "window_position.txt"
BTC_VALUE_FILE = "btc_value.txt"
THEME_COLOR_FILE = "theme_color.txt"
NOTEBOOK_FILE = "notes.txt"

# Define the path to this script for startup
APP_NAME = "BTC Pracker"
APP_PATH = os.path.abspath(__file__)

def set_startup(enable):
    """Set or remove this script from Windows startup."""
    try:
        key = winreg.HKEY_CURRENT_USER
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, reg_path, 0, winreg.KEY_ALL_ACCESS) as registry_key:
            if enable:
                winreg.SetValueEx(registry_key, APP_NAME, 0, winreg.REG_SZ, APP_PATH)
            else:
                winreg.DeleteValue(registry_key, APP_NAME)
    except WindowsError:
        pass
		
def calculate_percentage_change(start_price, current_price):
    """Calculate the percentage change between two prices."""
    if start_price == 0:
        return 0
    return ((current_price - start_price) / start_price) * 100

def display_live_percentage_change():
    """Fetch prices and display live percentage change in green or red based on selected timeframe."""
    global current_time_range

    # Fetch current price
    current_price = get_bitcoin_price_eur()
    if current_price is None:
        percent_label.config(text="Data Unavailable", fg="grey")
        return
    
    # Fetch historical price based on the selected timeframe
    historical_prices = get_historical_prices()
    if historical_prices:
        start_price = historical_prices[0][1]  # Assuming first price is the oldest price in the timeframe
    else:
        percent_label.config(text="Data Unavailable", fg="grey")
        return
    
    # Calculate percentage change
    percentage_change = calculate_percentage_change(start_price, current_price)
    
    # Set color based on positive or negative change
    color = "#82ef82" if percentage_change >= 0 else "#ff4d4d"
    
    # Update the label with the percentage change
    percent_label.config(text=f"{percentage_change:.2f}%", fg=color)
    
    # Repeat this function every 10 seconds
    percent_label.after(10000, display_live_percentage_change)
	
# Function to open a new "Notebook" window
def open_notebook():
    # Create a new top-level window
    notebook_window = Toplevel(root)
    notebook_window.title("Notebook")
    notebook_window.geometry("400x380")
    notebook_window.config(bg="#212121")

    # Text widget for writing notes
    text_area = Text(notebook_window, wrap="word", font=("Arial", 10), bg="#212121", fg="white", insertbackground="white")
    text_area.pack(expand=True, fill="both")

    # Load existing notes if the file exists
    if os.path.exists(NOTEBOOK_FILE):
        with open(NOTEBOOK_FILE, "r") as f:
            notes = f.read()
            text_area.insert("1.0", notes)

    # Save notes on closing the notebook window
    def save_notes():
        with open(NOTEBOOK_FILE, "w") as f:
            f.write(text_area.get("1.0", "end-1c"))
        notebook_window.destroy()

    notebook_window.protocol("WM_DELETE_WINDOW", save_notes)  # Save notes on window close

# Default and preset colors
preset_colors = ["#DAA520", "#62ffc2", "#62edff", "#ff6294", "#ff7e62"]
custom_colors = ["#F7931A", "#3AF23A", "#D4B461", "#3178C6", "#35B454"] * 5  # Initialize with placeholders for custom colors
theme_color = preset_colors[0]  # Default to 'goldenrod'

# Load saved color
if os.path.exists(THEME_COLOR_FILE):
    with open(THEME_COLOR_FILE, "r") as f:
        theme_color = f.read().strip()

# Time ranges for historical data
TIME_RANGES = {
    '12h': {'interval': 1, 'hours': 12},
    '31d': {'interval': 60, 'days': 31},
    '90d': {'interval': 240, 'days': 90},
    '365d': {'interval': 1440, 'days': 365},
    'YTD': {'interval': 1440, 'start_of_year': True},
    'ALL': {'interval': 10080, 'all': True}
}

current_time_range = '12h'

# Function to open the Options window
def open_options():
    global theme_color, current_time_range
    options_window = Toplevel(root)
    options_window.overrideredirect(1)
    options_window.geometry("400x500")
    options_window.config(bg="#212121")

    # Draggable functionality for options window
    def on_drag_start(event):
        options_window.x = event.x
        options_window.y = event.y

    def on_drag_motion(event):
        deltax = event.x - options_window.x
        deltay = event.y - options_window.y
        x = options_window.winfo_x() + deltax
        y = options_window.winfo_y() + deltay
        options_window.geometry(f"+{x}+{y}")

    options_window.bind('<Button-1>', on_drag_start)
    options_window.bind('<B1-Motion>', on_drag_motion)

    # Close button in the options window
    close_button = tk.Button(options_window, text='X', command=options_window.destroy, bg=theme_color, fg="black", borderwidth=0)
    close_button.config(font=('Arial', 12))
    close_button.place(x=380, y=10)

    # "Pick Theme" button in the options window
    theme_button = tk.Button(options_window, text="Pick Theme", command=pick_theme, bg=theme_color, fg="black", font=("Arial", 10))
    theme_button.pack(pady=10)

    # Radio buttons for time range selection
    tk.Label(options_window, text="Time Range @startup", bg="#212121", fg="white").pack(pady=10)
    time_range_var = tk.StringVar(value=current_time_range)
    for range_name in TIME_RANGES.keys():
        tk.Radiobutton(options_window, text=range_name, variable=time_range_var, value=range_name,
                       bg="#2A2A2A", fg="white", selectcolor=theme_color).pack(pady=2)
					   
    # BTC Address label (at the bottom, copyable with mouse)
    btc_address = "Not Set"  # Example BTC address
    btc_label = tk.Label(options_window, text="BTC Donations:", bg="#212121", fg="grey", font=("Arial", 9)).place(x=20, y=475)
	
    # Author label (centered at the top)
    author_label = tk.Label(options_window, text="a program by F.S (2024)", bg="#212121", fg="grey", font=("Arial", 9, "bold")).place(x=20, y=450)
	
    # BTC Address Entry (read-only, mouse-selectable for copying)
    btc_address_entry = tk.Entry(options_window, width=34, font=("Arial", 9), bg="#212121", fg="black", bd=0, insertbackground="#212121")
    btc_address_entry.insert(0, btc_address)
    btc_address_entry.config(state="readonly")  # Make the entry read-only
    btc_address_entry.place(x=120, y=475)

    # "Start with Windows" checkbox
    start_with_windows_var = IntVar(value=1 if is_startup_enabled() else 0)
    start_with_windows_checkbox = Checkbutton(options_window, text="Start with Windows", variable=start_with_windows_var,
                                              bg="#212121", fg="white", selectcolor="grey",
                                              command=lambda: set_startup(start_with_windows_var.get()))
    start_with_windows_checkbox.pack(pady=5)

    # Save button
    def save_options():
        global theme_color, current_time_range
        current_time_range = time_range_var.get()
        set_startup(start_with_windows_var.get())
        options_window.destroy()

    save_button = tk.Button(options_window, text="Save", command=save_options, bg=theme_color, fg="black")
    save_button.pack(pady=20)

    # Hover effects for Save button
    save_button.bind("<Enter>", lambda event: on_enter_button(event, save_button))
    save_button.bind("<Leave>", lambda event: on_leave_button(event, save_button))
	
    # Bind hover effects to "Pick Theme" button
    theme_button.bind("<Enter>", lambda event: on_enter_button(event, theme_button))
    theme_button.bind("<Leave>", lambda event: on_leave_button(event, theme_button))
	
	    # Bind hover effects to the close button
    close_button.bind("<Enter>", lambda event: on_enter_button(event, close_button))
    close_button.bind("<Leave>", lambda event: on_leave_button(event, close_button))
	
def is_startup_enabled():
    """Check if the app is set to start with Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
            return APP_PATH == winreg.QueryValueEx(key, APP_NAME)[0]
    except WindowsError:
        return False

def load_window_position():
    if os.path.exists(WINDOW_POSITION_FILE):
        with open(WINDOW_POSITION_FILE, "r") as f:
            try:
                x, y = map(int, f.read().strip().split(','))
                return x, y
            except ValueError:
                return None, None
    return None, None

def save_window_position(x, y):
    with open(WINDOW_POSITION_FILE, "w") as f:
        f.write(f"{x},{y}")

def get_bitcoin_price_eur():
    url = 'https://api.kraken.com/0/public/Ticker?pair=XBTEUR'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'result' in data and 'XXBTZEUR' in data['result']:
            return float(data['result']['XXBTZEUR']['c'][0])
    except requests.RequestException:
        return None

def get_historical_prices():
    global current_time_range
    time_range = TIME_RANGES[current_time_range]
    interval = time_range['interval']
    past_time = timedelta()

    if 'hours' in time_range:
        past_time = timedelta(hours=time_range['hours'])
    elif 'days' in time_range:
        past_time = timedelta(days=time_range['days'])
    elif 'start_of_year' in time_range:
        start_of_year = datetime(datetime.now().year, 1, 1)
        past_time = datetime.now() - start_of_year
    elif 'all' in time_range:
        past_time = timedelta(days=365 * 5)

    url = f'https://api.kraken.com/0/public/OHLC?pair=XBTEUR&interval={interval}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'result' in data and 'XXBTZEUR' in data['result']:
            prices = data['result']['XXBTZEUR']
            return [(datetime.fromtimestamp(int(price[0])), float(price[4])) for price in prices]
    except requests.RequestException:
        return []
    return []

def get_recent_trades():
    url = 'https://api.kraken.com/0/public/Trades?pair=XBTEUR&count=120000'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'result' in data and 'XXBTZEUR' in data['result']:
            trades = data['result']['XXBTZEUR']
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=24)

            recent_prices = [float(trade[0]) for trade in trades if datetime.fromtimestamp(trade[2]) > cutoff_time]
            return recent_prices
    except requests.RequestException:
        return []
    return []

def save_btc_value(value):
    with open(BTC_VALUE_FILE, "w") as f:
        f.write(str(value))

def load_btc_value():
    if os.path.exists(BTC_VALUE_FILE):
        with open(BTC_VALUE_FILE, "r") as f:
            return float(f.read().strip())
    return 0.0

def update_conversion(event=None):
    try:
        btc_amount = float(btc_entry.get())
        btc_to_eur_rate = get_bitcoin_price_eur()
        eur_value = btc_amount * btc_to_eur_rate
        conversion_label.config(text=f"{eur_value:.2f} EUR")
        save_btc_value(btc_amount)
    except ValueError:
        conversion_label.config(text="Invalid input")

# Initialize the last price variable
last_price = get_bitcoin_price_eur() or 0.0

def animate_price_change(label, start_price, end_price, duration=150, steps=50):#Duration in Ms, steps is how much spins
    """Animate the price label to simulate a spinning slot machine effect."""
    # Calculate the price increment for each step
    price_difference = end_price - start_price
    step_value = price_difference / steps
    delay = duration // steps

    def update_price(step=0):
        """Update the label text with the next step in the animation."""
        if step <= steps:
            # Calculate the current price based on step
            current_price = start_price + step_value * step
            label.config(text=f"₿itcoin: €{current_price:.2f}")
            
            # Schedule the next step
            label.after(delay, update_price, step + 1)
        else:
            # Set the final price to ensure accuracy
            label.config(text=f"₿itcoin: €{end_price:.2f}")

    # Start the animation
    update_price()

def update_price_label(label):
    """Fetch the current price and animate the price change."""
    global last_price
    current_price = get_bitcoin_price_eur()
    if current_price is not None:
        # Animate the price change from last_price to current_price
        animate_price_change(label, last_price, current_price)
        last_price = current_price  # Update last price to current after animation

    # Schedule the next update
    label.after(10000, lambda: update_price_label(label))

def plot_historical_prices(ax):
    historical_prices = get_historical_prices()
    recent_prices = get_recent_trades()

    if historical_prices:
        new_dates, new_prices = zip(*historical_prices)
        ax.clear()
        ax.set_facecolor('#212121')
        ax.plot(new_dates, new_prices, label='Bitcoin Price (EUR)', color=theme_color)

        if recent_prices:
            median_price = np.median(recent_prices)
            ax.axhline(y=median_price, color='white', linestyle='--', linewidth=0.5)
            ax.text(1, 1.06, f'~24h €{median_price:.2f}', transform=ax.transAxes, color='white', fontsize=9, verticalalignment='top', ha='right')

        ax.spines[:].set_color(theme_color)
        ax.set_ylabel('EUR', color=theme_color)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M' if current_time_range == '12h' else '%d-%m' if current_time_range == '31d' else '%d-%m' if current_time_range == '90d' else '%m-%y'))
        ax.grid(color=theme_color, linestyle='--', linewidth=0.5)
        ax.tick_params(axis='both', colors=theme_color)

        canvas.draw()

def zoom(event):
    current_xlim = ax.get_xlim()
    current_ylim = ax.get_ylim()
    mouse_x, mouse_y = event.x, event.y
    x_data, y_data = ax.transData.inverted().transform((mouse_x, mouse_y))
    zoom_scale = 0.9 if event.delta > 0 else 1.1

    new_xlim = [x_data - (x_data - current_xlim[0]) * zoom_scale,
                x_data + (current_xlim[1] - x_data) * zoom_scale]
    new_ylim = [y_data - (y_data - current_ylim[0]) * zoom_scale,
                y_data + (current_ylim[1] - y_data) * zoom_scale]

    ax.set_xlim(new_xlim)
    ax.set_ylim(new_ylim)
    canvas.draw()

def update_graph():
    plot_historical_prices(ax)
    root.after(60000, update_graph)

def change_time_range(event):
    global current_time_range
    current_time_range = time_range_var.get()
    plot_historical_prices(ax)

def pick_theme():
    color_picker = tk.Toplevel(root)
    color_picker.title("Pick Theme Color")
    color_picker.geometry("240x100")
    color_picker.config(bg="#212121")

    def set_theme_color(color):
        global theme_color
        theme_color = color
        save_theme_color(color)
        update_theme()
        color_picker.destroy()

    def save_theme_color(color):
        with open(THEME_COLOR_FILE, "w") as f:
            f.write(color)

    for i, color in enumerate(preset_colors + custom_colors):
        color_button = tk.Button(color_picker, bg=color, width=4, height=2, command=lambda col=color: set_theme_color(col))
        color_button.grid(row=i // 5, column=i % 5, padx=5, pady=5)
		
# Define colors for hover and normal state
HOVER_COLOR = "white"  # White for hover effect
BUTTON_COLOR = theme_color  # Default button color

# Function to change button color on hover
def on_enter_button(event, button):
    button.config(bg=HOVER_COLOR)

# Function to revert button color when hover ends
def on_leave_button(event, button):
    button.config(bg=theme_color)
	
def update_theme():
    price_label.config(fg=theme_color)
    time_range_dropdown.config(bg=theme_color, fg="black")
    close_button.config(bg=theme_color, fg="black")
    theme_button.config(bg=theme_color, fg="black")
    notebook_button.config(bg=theme_color, fg="black")
    options_button.config(bg=theme_color, fg="black")  # Ensure options button updates color
    plot_historical_prices(ax)
    button.config(bg=theme_color)
	
# Function to fetch the Fear and Greed Index
def get_fear_and_greed_index():
    url = 'https://api.alternative.me/fng/?limit=1'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            index_value = int(data['data'][0]['value'])
            return index_value, data['data'][0]['value_classification']
    except requests.RequestException:
        return None, "Error"

# Function to update Fear and Greed Index display
def update_fear_and_greed_display():
    index, classification = get_fear_and_greed_index()
    
    if index is not None:
        fg_color = "#ff4d4d" if index < 45 else "#ffb84d" if index < 60 else "#82ef82"
        fear_greed_label.config(text=f"{index} {classification}", fg=fg_color)
    else:
        fear_greed_label.config(text="N/A", fg="grey")
    
    fear_greed_label.after(60000, update_fear_and_greed_display)  # Update every minute
	
if __name__ == "__main__":
    root = tk.Tk()
    root.overrideredirect(1)
    root.geometry("640x400")
    root.config(bg="#212121")

    last_x, last_y = load_window_position()
    if last_x is not None and last_y is not None:
        root.geometry(f"+{last_x}+{last_y}")
    else:
        root.update_idletasks()
        width, height = root.winfo_width(), root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

    frame = tk.Frame(root, bg="#212121")
    frame.pack(expand=True)

# Example usage for displaying Bitcoin price
    price_label = tk.Label(frame, text=f"₿itcoin: €{last_price:.2f}", font=('Arial', 22), bg="#212121", fg=theme_color)
    price_label.pack(pady=10)

# Start the price update loop with animation
    update_price_label(price_label)
	

    fig, ax = plt.subplots(figsize=(25, 6), dpi=100)
    fig.patch.set_facecolor('#212121')
    ax.set_facecolor('#212121')
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()

    time_range_var = tk.StringVar(root)
    time_range_var.set(current_time_range)
    time_range_dropdown = tk.OptionMenu(root, time_range_var, *TIME_RANGES.keys(), command=change_time_range)
    time_range_dropdown.config(bg=theme_color, fg="black", font=("Arial", 12), borderwidth=0, highlightthickness=0)
    time_range_dropdown.place(x=10, y=10)

	
    # "Notebook" button setup next to dropdown menu
    notebook_button = tk.Button(root, text="Notebook", command=open_notebook, bg=theme_color, fg="black", font=("Arial", 10))
    notebook_button.place(x=40, y=45)  # Adjust `x` position if needed
	
    # "Options" button setup
    options_button = tk.Button(root, text="⸎", command=open_options, bg=theme_color, fg="black", font=("Arial", 10))
    options_button.place(x=10, y=45) # Adjust position as needed

    btc_value = load_btc_value()
    conversion_frame = tk.Frame(root, bg="#212121")
    conversion_frame.place(x=220, y=50)

    btc_label = tk.Label(conversion_frame, text="BTC :", bg="#212121", fg="grey", font=("Arial", 10))
    btc_label.pack(side="left")

    btc_entry = tk.Entry(conversion_frame, bg="#212121", fg="grey", width=12)
    btc_entry.insert(0, str(btc_value))
    btc_entry.pack(side="left", padx=5)

    conversion_label = tk.Label(conversion_frame, text="0 EUR", bg="#212121", fg="grey", font=("Arial", 10))
    conversion_label.pack(side="left")

    btc_entry.bind("<KeyRelease>", update_conversion)

    # Add labels for displaying the highest and lowest prices
    high_label = tk.Label(root, text="Loading...", fg="olive", bg="#212121", font=("Next Art", 10))
    high_label.place(x=10, y=76)  # Adjust x and y to position it next to the dropdown

    #low_label = tk.Label(root, text="Loading...", fg="peru", bg="#212121", font=("Next Art", 10))
    #low_label.place(x=10, y=367)  # Adjust x and y to position it next to the dropdown

    # Create label for Fear and Greed Index
    fear_greed_label = tk.Label(root, text="F/G-I Loading...", font=("Next Art", 10), bg="#212121")
    fear_greed_label.place(x=495, y=60)  # Position over 24h

    # Call the update function to initialize the display
    update_fear_and_greed_display()
    def update_conversion_periodically():
        update_conversion()
        root.after(10000, update_conversion_periodically)

    update_conversion_periodically()
    update_price_label(price_label)
    plot_historical_prices(ax)
    canvas_widget.bind("<MouseWheel>", zoom)
    update_graph()

    def on_closing():
        save_window_position(root.winfo_x(), root.winfo_y())
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    close_button = tk.Button(root, text='X', command=on_closing, bg=theme_color, fg='black', borderwidth=0)
    close_button.config(font=('Arial', 12))
    close_button.place(x=605, y=15)
	

	
    # Bind hover effects to "Options" button
    options_button.bind("<Enter>", lambda event: on_enter_button(event, options_button))
    options_button.bind("<Leave>", lambda event: on_leave_button(event, options_button))
	
    # Bind hover effects to "Notebook" button
    notebook_button.bind("<Enter>", lambda event: on_enter_button(event, notebook_button))
    notebook_button.bind("<Leave>", lambda event: on_leave_button(event, notebook_button))

    # Bind hover effects to the close button
    close_button.bind("<Enter>", lambda event: on_enter_button(event, close_button))
    close_button.bind("<Leave>", lambda event: on_leave_button(event, close_button))

def update_conversion_reverse(event=None):
    try:
        eur_amount = float(eur_entry.get())
        btc_to_eur_rate = get_bitcoin_price_eur()
        btc_value = eur_amount / btc_to_eur_rate if btc_to_eur_rate else 0
        reverse_conversion_label.config(text=f"{btc_value:.6f} BTC")
    except ValueError:
        reverse_conversion_label.config(text="Invalid input")
		
# Initialize the percentage label at the specified coordinates
percent_label = tk.Label(root, text="", font=("Next Art", 10), bg="#212121")
percent_label.place(x=450, y=10)

# Call the function to start live updates
display_live_percentage_change()

# EUR-to-BTC conversion UI
reverse_conversion_frame = tk.Frame(root, bg="#212121")
reverse_conversion_frame.place(x=218, y=75)  # Position below the first BTC-to-EUR calculator

# Label for EUR input
eur_label = tk.Label(reverse_conversion_frame, text="EUR :", bg="#212121", fg="grey", font=("Arial", 10))
eur_label.pack(side="left")

# Entry for EUR input
eur_entry = tk.Entry(reverse_conversion_frame, bg="#212121", fg="grey", width=12)
eur_entry.pack(side="left", padx=5)

# Label to display BTC result
reverse_conversion_label = tk.Label(reverse_conversion_frame, text="0 BTC", bg="#212121", fg="grey", font=("Arial", 10))
reverse_conversion_label.pack(side="left")

# Bind the update function to the EUR entry field
eur_entry.bind("<KeyRelease>", update_conversion_reverse)

# Functions for window dragging
def on_drag_start(event):
    root.x = event.x
    root.y = event.y

def on_drag_motion(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")

root.bind('<Button-1>', on_drag_start)
root.bind('<B1-Motion>', on_drag_motion)

def show_window():
    root = tk.Tk()
    
    # Fenster ohne Dekoration erstellen
    root.overrideredirect(True)
    # Stelle sicher, dass das Fenster in der Taskleiste angezeigt wird
hwnd = ctypes.windll.user32.GetForegroundWindow()  # Aktuelles Fensterhandle bekommen
    
    # GetWindowLongPtr für 64-Bit Unterstützung
get_window_long = ctypes.windll.user32.GetWindowLongPtrW
set_window_long = ctypes.windll.user32.SetWindowLongPtrW

    # Aktuellen Fensterstil abrufen
style = get_window_long(hwnd, -20)  # -20 ist GWL_EXSTYLE

    # Setze den neuen Fensterstil
set_window_long(hwnd, -20, style | 0x00040000 | 0x00000040)  # WS_EX_APPWINDOW und WS_EX_TOOLWINDOW entfernen

def update_high_low():
    """Fetch historical prices and update the high and low labels."""
    historical_prices = get_historical_prices()

    if historical_prices:
        prices = [price[1] for price in historical_prices]
        highest_price = max(prices)
        #lowest_price = min(prices)
        
        high_label.config(text=f"Top: {highest_price:.2f}€")
        #low_label.config(text=f"Low: {lowest_price:.2f}€")
    else:
        high_label.config(text="High: N/A")
        #low_label.config(text="Low: N/A")
    
    # Schedule the next update in 60 seconds
    root.after(2000, update_high_low)

# Initial call to display the first high/low values
update_high_low()

	
root.mainloop()
