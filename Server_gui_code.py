import threading
from flask import Flask, request
import tkinter as tk
from math import sqrt

# ---- Flask server ----
app = Flask(__name__)

sensor_data = {}        # key: gui_node_number, value: sensor data dict
assigned_nodes = {}     # key: ESP32 IP, value: gui_node_number
next_node_number = 1
ALERT_QUORUM = 2        # Minimum nodes to trigger network alert

@app.route("/data", methods=["POST"])
def data():
    global sensor_data, assigned_nodes, next_node_number

    data = request.json
    node_ip = request.remote_addr  # Use ESP32 IP as unique key

    if node_ip not in assigned_nodes:
        assigned_nodes[node_ip] = next_node_number
        next_node_number += 1

    gui_node = assigned_nodes[node_ip]
    data['ip'] = node_ip
    sensor_data[gui_node] = data

    return "OK"

# ---- Tkinter GUI ----
def update_gui():
    for widget in frame.winfo_children():
        widget.destroy()

    # Headers
    headers = ["Node", "IP", "AX", "AY", "AZ", "Magnitude", "ALERT"]
    header_font = ("Arial", 14, "bold")
    cell_font = ("Arial", 13)
    
    for col, text in enumerate(headers):
        tk.Label(frame, text=text, font=header_font, borderwidth=1, relief="solid",
                 width=14, bg="#2F4F4F", fg="white").grid(row=0, column=col, padx=2, pady=2)

    row = 1
    alerts = 0
    for gui_node, data in sensor_data.items():
        ax, ay, az = data['ax'], data['ay'], data['az']
        magnitude = sqrt(ax*2 + ay*2 + az*2)

        bg_color = "#E0FFFF" if row % 2 == 0 else "#B0E0E6"  # alternating row colors

        tk.Label(frame, text=f"{gui_node}", width=14, font=cell_font, borderwidth=1, relief="solid",
                 bg=bg_color).grid(row=row, column=0, padx=2, pady=2)
        tk.Label(frame, text=f"{data['ip']}", width=14, font=cell_font, borderwidth=1, relief="solid",
                 bg=bg_color).grid(row=row, column=1, padx=2, pady=2)
        tk.Label(frame, text=f"{ax:.2f}", width=14, font=cell_font, borderwidth=1, relief="solid",
                 bg=bg_color).grid(row=row, column=2, padx=2, pady=2)
        tk.Label(frame, text=f"{ay:.2f}", width=14, font=cell_font, borderwidth=1, relief="solid",
                 bg=bg_color).grid(row=row, column=3, padx=2, pady=2)
        tk.Label(frame, text=f"{az:.2f}", width=14, font=cell_font, borderwidth=1, relief="solid",
                 bg=bg_color).grid(row=row, column=4, padx=2, pady=2)
        tk.Label(frame, text=f"{magnitude:.2f}", width=14, font=cell_font, borderwidth=1, relief="solid",
                 bg=bg_color).grid(row=row, column=5, padx=2, pady=2)

        # Color-coded ALERT
        alert_label = tk.Label(frame, text="ALERT" if data['alert'] else "", width=14, font=cell_font,
                               fg="white", bg="red" if data['alert'] else "green", borderwidth=1, relief="solid")
        alert_label.grid(row=row, column=6, padx=2, pady=2)

        if data['alert']:
            alerts += 1
        row += 1

    # Network alert on top
    if alerts >= ALERT_QUORUM:
        network_alert.set("⚠ NETWORK ALERT! Multiple nodes triggered ⚠")
    else:
        network_alert.set("")

    root.after(200, update_gui)

def start_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# ---- GUI setup ----
root = tk.Tk()
root.title("Multi-node ESP32 Sensor Monitor")
root.geometry("1000x450")
root.minsize(900, 400)
root.configure(bg="#4682B4")   # Background color for the entire window
root.state('zoomed')           # Start maximized

network_alert = tk.StringVar()
tk.Label(root, textvariable=network_alert, fg="white", bg="#8B0000",
         font=("Arial", 18, "bold"), pady=10).pack(fill="x")

frame = tk.Frame(root, bg="#4682B4")
frame.pack(expand=True, fill="both", padx=10, pady=5)

# ---- Start Flask server in background ----
threading.Thread(target=start_flask, daemon=True).start()
update_gui()
root.mainloop()