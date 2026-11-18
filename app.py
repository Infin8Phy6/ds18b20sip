import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time

class TempControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Temperature Monitor & Control")
        self.root.geometry("450x390")
        self.root.config(bg="#121212")

        self.ser = None
        self.running = False

        # Styling
        style = ttk.Style()
        style.theme_use('clam')

        # Title
        title_lbl = tk.Label(root, text="ESP32 DS18B20 Dashboard", font=("Arial", 16, "bold"), fg="#90caf9", bg="#121212")
        title_lbl.pack(pady=15)

        # Connection Frame
        conn_frame = tk.Frame(root, bg="#121212")
        conn_frame.pack(pady=5)

        tk.Label(conn_frame, text="COM Port:", fg="#fff", bg="#121212", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo = ttk.Combobox(conn_frame, values=ports, width=15)
        if ports:
            self.port_combo.current(0)
        self.port_combo.pack(side=tk.LEFT, padx=5)

        self.connect_btn = tk.Button(conn_frame, text="Connect", command=self.toggle_connection, bg="#4caf50", fg="white", font=("Arial", 10, "bold"), width=10)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        # Temperature Display Card
        temp_frame = tk.Frame(root, bg="#1e1e1e", bd=2, relief=tk.GROOVE)
        temp_frame.pack(pady=20, padx=20, fill=tk.X)

        tk.Label(temp_frame, text="Live Sensor Reading", font=("Arial", 11), fg="#bbb", bg="#1e1e1e").pack(pady=5)
        
        self.temp_c_lbl = tk.Label(temp_frame, text="-- °C", font=("Arial", 32, "bold"), fg="#4caf50", bg="#1e1e1e")
        self.temp_c_lbl.pack()

        self.temp_f_lbl = tk.Label(temp_frame, text="-- °F", font=("Arial", 14), fg="#81c784", bg="#1e1e1e")
        self.temp_f_lbl.pack(pady=(0, 10))

        # Control Frame
        ctrl_frame = tk.Frame(root, bg="#121212")
        ctrl_frame.pack(pady=10)

        tk.Label(ctrl_frame, text="Output Control (Relay / LED):", fg="#fff", bg="#121212", font=("Arial", 11)).pack(anchor=tk.W, pady=5)
        
        btn_box = tk.Frame(ctrl_frame, bg="#121212")
        btn_box.pack()

        self.on_btn = tk.Button(btn_box, text="Turn ON", command=lambda: self.send_control(1), bg="#2e7d32", fg="white", width=12, font=("Arial", 10, "bold"), state=tk.DISABLED)
        self.on_btn.pack(side=tk.LEFT, padx=10)

        self.off_btn = tk.Button(btn_box, text="Turn OFF", command=lambda: self.send_control(0), bg="#c62828", fg="white", width=12, font=("Arial", 10, "bold"), state=tk.DISABLED)
        self.off_btn.pack(side=tk.LEFT, padx=10)

        # Status Bar
        self.status_lbl = tk.Label(root, text="Status: Disconnected", fg="#ef5350", bg="#121212", font=("Arial", 9))
        self.status_lbl.pack(side=tk.BOTTOM, pady=10)

    def toggle_connection(self):
        if self.ser is None or not self.ser.is_open:
            port = self.port_combo.get()
            if not port:
                messagebox.showerror("Error", "Please select a valid COM port.")
                return
            try:
                self.ser = serial.Serial(port, 115200, timeout=1)
                time.sleep(2) # Give ESP32 time to initialize
                self.running = True
                self.connect_btn.config(text="Disconnect", bg="#c62828")
                self.status_lbl.config(text=f"Status: Connected to {port}", fg="#66bb6a")
                self.on_btn.config(state=tk.NORMAL)
                self.off_btn.config(state=tk.NORMAL)
                
                # Start background polling thread
                threading.Thread(target=self.poll_loop, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            self.running = False
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.connect_btn.config(text="Connect", bg="#4caf50")
            self.status_lbl.config(text="Status: Disconnected", fg="#ef5350")
            self.on_btn.config(state=tk.DISABLED)
            self.off_btn.config(state=tk.DISABLED)
            self.temp_c_lbl.config(text="-- °C")
            self.temp_f_lbl.config(text="-- °F")

    def poll_loop(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                self.ser.write(b"GET\n")
                line = self.ser.readline().decode('utf-8').strip()
                if line.startswith("TEMP:"):
                    val = line.split(":")[1]
                    if val != "ERROR":
                        c = float(val)
                        f = (c * 9/5) + 32
                        self.root.after(0, self.update_display, c, f)
            except Exception:
                pass
            time.sleep(2)

    def update_display(self, c, f):
        self.temp_c_lbl.config(text=f"{c:.2f} °C")
        self.temp_f_lbl.config(text=f"{f:.2f} °F")

    def send_control(self, state):
        if self.ser and self.ser.is_open:
            try:
                cmd = f"RELAY:{state}\n"
                self.ser.write(cmd.encode('utf-8'))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send command: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TempControlApp(root)
    root.mainloop()