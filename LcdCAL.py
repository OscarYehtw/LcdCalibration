import tkinter as tk
from tkinter import font, messagebox, ttk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import colour
from matplotlib.legend_handler import HandlerPatch
from matplotlib.patches import Ellipse, Patch, PathPatch
import mpld3
from mpld3 import plugins
from matplotlib.path import Path
from matplotlib.lines import Line2D
import os
import numpy as np
import sys
import csv
from datetime import datetime
import time
import platform
import subprocess
from PIL import Image, ImageTk
#from ch341.ch341 import enable_leds
from cli.cli import detect_com_ports, enable_lcd, _uart
#from set_led_color import set_led_color_ch341
#from cl200a_controller import CL200A

class TickStylePlugin(plugins.PluginBase):
    JAVASCRIPT = """
    mpld3.register_plugin("tickstyle", TickStylePlugin);
    TickStylePlugin.prototype = Object.create(mpld3.Plugin.prototype);
    TickStylePlugin.prototype.constructor = TickStylePlugin;
    function TickStylePlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
        this.fig = fig;
    }
    TickStylePlugin.prototype.draw = function(){
        d3.selectAll("g.tick line").style("stroke-dasharray", "2,2")
                                   .style("stroke-width", "0.5")
                                   .style("stroke", "gray");
    };
    """
    def __init__(self):
        self.dict_ = {"type": "tickstyle"}

class CrosshairPlugin(plugins.PluginBase):
    JAVASCRIPT = """
    mpld3.register_plugin("crosshair", CrosshairPlugin);
    CrosshairPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    CrosshairPlugin.prototype.constructor = CrosshairPlugin;

    function CrosshairPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
        this.fig = fig;
        this.ax = fig.axes[0];
    }

    CrosshairPlugin.prototype.draw = function(){
        var fig = this.fig;
        var ax = this.ax;

        // var svg = d3.select(fig.canvas);
        var svg = d3.select("svg.mpld3-figure");

        var width = +svg.attr("width");
        var height = +svg.attr("height");

        this.vline = svg.append("line")
            .attr("stroke", "gray")
            .attr("stroke-width", 1)
            .attr("pointer-events", "none")
            .style("display", "none");

        this.hline = svg.append("line")
            .attr("stroke", "gray")
            .attr("stroke-width", 1)
            .attr("pointer-events", "none")
            .style("display", "none");

        var vline = this.vline;
        var hline = this.hline;

        svg.on("mousemove", function(event){
            var coords = d3.mouse(this);
            var x = ax.x.invert(coords[0]);
            var y = ax.y.invert(coords[1]);

            if(x < 0 || x > 0.7 || y < 0 || y > 0.7){
                vline.style("display", "none");
                hline.style("display", "none");
                return;
            }

            var px = ax.x(x);
            var py = ax.y(y);

            vline
                .attr("x1", px).attr("y1", 0)
                .attr("x2", px).attr("y2", height)
                .style("display", null);

            hline
                .attr("x1", 0).attr("y1", py)
                .attr("x2", width).attr("y2", py)
                .style("display", null);
        });

        svg.on("mouseleave", function(){
            vline.style("display", "none");
            hline.style("display", "none");
        });
    };
    """

    def __init__(self):
        self.dict_ = {"type": "crosshair"}

class MousePositionPlugin(plugins.PluginBase):
    """Plugin to display u′ and v′ coordinates on hover (D3 v3 compatible)."""
    JAVASCRIPT = """
    mpld3.register_plugin("mouseposition", MousePositionPlugin);
    MousePositionPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    MousePositionPlugin.prototype.constructor = MousePositionPlugin;

    function MousePositionPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
        this.fig = fig;
    }

    MousePositionPlugin.prototype.draw = function(){
        var fig = this.fig;
        var ax = fig.axes[0];

        var coordsDiv = document.createElement("div");
        coordsDiv.style.position = "absolute";
        coordsDiv.style.top = "10px";
        coordsDiv.style.left = "10px";
        coordsDiv.style.padding = "5px 8px";
        coordsDiv.style.background = "rgba(255,255,255,0.9)";
        coordsDiv.style.border = "1px solid #ccc";
        coordsDiv.style.borderRadius = "5px";
        coordsDiv.style.font = "12px sans-serif";
        coordsDiv.style.zIndex = 1000;
        coordsDiv.innerHTML = "u′ = ---, v′ = ---";
        document.body.appendChild(coordsDiv);

        fig.canvas.on("mousemove", function(){
            var rect = this.getBoundingClientRect();
            var mouseX = d3.event.clientX - rect.left;
            var mouseY = d3.event.clientY - rect.top;

            var x = ax.x.invert(mouseX - ax.position[0]);
            var y = ax.y.invert(mouseY - ax.position[1]);

            if (x >= 0 && x <= 0.7 && y >= 0 && y <= 0.7) {
                coordsDiv.innerHTML = "u′ = " + x.toFixed(4) + ", v′ = " + y.toFixed(4);
                coordsDiv.style.display = "block";
            } else {
                coordsDiv.style.display = "none";
            }
        });

        fig.canvas.on("mouseleave", function(){
            coordsDiv.innerHTML = "u′ = ---, v′ = ---";
            coordsDiv.style.display = "block";
        });
    };
    """
    def __init__(self):
        self.dict_ = {"type": "mouseposition"}

class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + cy + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("tahoma", "9", "normal")
        )
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

CONFIG_FILE = "config.json"

def adjust_u_prime_with_pid(r, g, b, delta_u, pid_r, pid_g, pid_b):
    dr = pid_r.compute(delta_u) * r
    dg = pid_g.compute(-delta_u) * g
    db = pid_b.compute(-delta_u) * b
    return r + dr, g + dg, b + db

def adjust_v_prime_with_pid(r, g, b, delta_v, pid_r, pid_g, pid_b):
    dr = pid_r.compute(-delta_v) * r
    dg = pid_g.compute(delta_v) * g
    db = pid_b.compute(-delta_v) * b
    return r + dr, g + dg, b + db

def adjust_u_prime_percentage(r, g, b, delta_u):
    factor = abs(delta_u) * 100
    if delta_u > 0:
        new_r = r * (1 + 0.07 * factor)
        new_g = g * (1 - 0.03 * factor)
        new_b = b * (1 - 0.02 * factor)
    else:
        new_r = r * (1 - 0.07 * factor)
        new_g = g * (1 + 0.03 * factor)
        new_b = b * (1 + 0.02 * factor)
    return new_r, new_g, new_b

def adjust_v_prime_percentage(r, g, b, delta_v):
    factor = abs(delta_v) * 100
    if delta_v > 0:
        new_r = r * (1 - 0.03 * factor)
        new_g = g * (1 + 0.12 * factor)
        new_b = b * (1 - 0.15 * factor)
    else:
        new_r = r * (1 + 0.03 * factor)
        new_g = g * (1 - 0.12 * factor)
        new_b = b * (1 + 0.05 * factor)
    return new_r, new_g, new_b

def clamp(v, min_val=0, max_val=255):
    return int(max(min_val, min(max_val, round(v))))

def closest_point_on_ellipse(px, py, cx, cy, major, minor, angle_deg, steps=360):
    steps = int(steps)  # Ensure steps is an integer
    angle = np.radians(angle_deg)
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    best_dist = float("inf")
    best_point = (cx, cy)
    for theta in np.linspace(0, 2 * np.pi, steps):
        ex = major / 2 * np.cos(theta)
        ey = minor / 2 * np.sin(theta)
        x_rot = cos_a * ex - sin_a * ey
        y_rot = sin_a * ex + cos_a * ey
        ex_final = cx + x_rot
        ey_final = cy + y_rot
        dist = np.hypot(ex_final - px, ey_final - py)
        if dist < best_dist:
           best_dist = dist
           best_point = (ex_final, ey_final)
    return best_point

def estimate_rgb_delta(target_uv, current_rgb):
    r0, g0, b0 = current_rgb
    u0, v0 = rgb_to_uv(r0, g0, b0)
    du = target_uv[0] - u0
    dv = target_uv[1] - v0
    eps = 1.0
    J = []
    for delta in [(eps, 0, 0), (0, eps, 0), (0, 0, eps)]:
        r1 = clamp(r0 + delta[0])
        g1 = clamp(g0 + delta[1])
        b1 = clamp(b0 + delta[2])
        u1, v1 = rgb_to_uv(r1, g1, b1)
        J.append([u1 - u0, v1 - v0])
    J = np.array(J).T
    try:
        delta_rgb = np.linalg.lstsq(J, [du, dv], rcond=None)[0]
        return (
            clamp(r0 + delta_rgb[0]),
            clamp(g0 + delta_rgb[1]),
            clamp(b0 + delta_rgb[2])
        )
    except Exception:
        return r0, g0, b0

def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def rgb_to_uv(r, g, b):
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)
    X = 0.4124 * r_lin + 0.3576 * g_lin + 0.1805 * b_lin
    Y = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    Z = 0.0193 * r_lin + 0.1192 * g_lin + 0.9505 * b_lin
    denom = X + 15 * Y + 3 * Z
    if denom == 0:
        return 0.0, 0.0
    u_prime = (4 * X) / denom
    v_prime = (9 * Y) / denom
    return u_prime, v_prime

class PIDController:
    def __init__(self, kp=1.0, ki=0.0, kd=0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0

    def reset(self):
        self.prev_error = 0
        self.integral = 0

    def compute(self, error):
        self.integral += error
        derivative = error - self.prev_error
        output = (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )
        self.prev_error = error
        return output

class CalibrationApp:
    def build_ellipse_centers_from_excel(self):
        df = pd.read_excel(self.xlsx_path, sheet_name="LCD SPEC", header=None)
        centers = {}

        for i in range(len(df)):
            try:
                desc = str(df.iat[i, 0]).strip()
                if "Center Coordinates" in desc and "Limit of" in desc:
                    color = desc.split("Limit of")[-1].strip().replace("'", "")
                    coord_str = str(df.iat[i, 1]).strip()
                    if "," in coord_str:
                        x, y = map(float, coord_str.split(","))
                        centers[color] = (x, y)
                        #print(f"[ELLIPSE] {color}: x={x}, y={y}")
            except Exception as e:
                #print(f"[DEBUG] Failed to parse row {i}: {e}")
                continue

        self.ellipse_centers = centers

    def __init__(self, root):
        self.root = root
        self.root.title("CIE1976 Utility")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.cover_lenses = ["None", "Black", "Silver", "WarmGold"]
        self.selected_cover_lens = tk.StringVar(value="None")
        
        #self.colors = ["Green", "Blue", "Yellow", "Orange", "White", "Purple"]
        self.color_rgb_map = {
            "Orange":  (255, 163, 134),  # #FFA386
            "Blue":    (184, 211, 254),  # #B8D3FE
            "Green":   (0, 216, 99),     # #00D863
            "Red":     (238, 103, 92),   # #EE675C
            "Yellow":  (253, 214, 99),   # #FDD663
            "White":   (255, 255, 255),  # #FFFFFF
            "Gray":    (128, 134, 139),  # #80868B
            "Purple":  (128, 0, 128),    # #800080
            "Black":   (0, 0, 0),        # #000000
        }
        self.color_hotkeys = {
            "Orange": "o",
            "Blue":   "b",
            "Green":  "g",
            "Red":    "r",
            "Yellow": "y",
            "White":  "w",
            "Gray":   "a",   # g 已被 Green 用
            "Purple": "p",
            "Black":  "k",   # b 已被 Blue 用
        }

        self.colors = list(self.color_rgb_map.keys())

        self.led_count = 8

        self.selected_led = tk.IntVar(value=1)
        #self.selected_color = tk.StringVar(value=self.colors[0])
        self.selected_color = tk.StringVar(value="White")

        self.r_value = tk.StringVar()
        self.g_value = tk.StringVar()
        self.b_value = tk.StringVar()

        self.point_counter = 1
        self.points = []
        self.plotted_points = []
        self.plotted_labels = []

        self.result_labels_shown = set()
        self.pass_fail_points = []

        style = ttk.Style()
        style.theme_use('default')

        style.configure("TNotebook.Tab",
                        font=("Arial", 8),
                        padding=[10, 5],
                        foreground="#888888",
                        background="#e0e0e0")

        style.map("TNotebook.Tab",
                  foreground=[("selected", "#444444")],
                  background=[("selected", "#ffffff")],
                  font=[("selected", ("Arial", 8, "bold underline"))])
        
        style.layout("TNotebook.Tab", [
            ('Notebook.tab', {
                'sticky': 'nswe',
                'children': [
                    ('Notebook.padding', {
                        'side': 'top',
                        'sticky': 'nswe',
                        'children': [
                            ('Notebook.label', {'side': 'top', 'sticky': ''})
                        ]
                    })
                ]
            })
        ])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        logo_path = os.path.join(os.path.dirname(__file__), "Luxshare640.png")
        if os.path.exists(logo_path):
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((150, 40), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
        else:
            self.logo_photo = None

        #self.xlsx_path = "BRW4 LED Spec_V02.xlsx"
        self.xlsx_path = "CF0F LCD Spec_V02_xy.xlsx"
        if not os.path.exists(self.xlsx_path):
            raise FileNotFoundError("Missing CF0F LCD Spec_V02_xy.xlsx")

        self.build_ellipse_centers_from_excel()

        self.csv_path = "data_dut_pwm_uv.csv"
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError("Missing data_dut_pwm_uv.csv")

        #self.cl200a_path = "cl200a_data.csv"
        self.cs160_path = "cs-160.csv"
        self.calibrated_path = "calibrated.csv"
        #self.calibrated_bin_path = "calibrated.bin"

        #self.viewer_frame = ttk.Frame(self.notebook)
        self.calibration_frame = ttk.Frame(self.notebook)
        #self.csv_viewer_frame = ttk.Frame(self.notebook)
        #self.bin_viewer_frame = ttk.Frame(self.notebook)

        #self.notebook.add(self.viewer_frame, text="CIE1976 Viewer")

        self.viewer_frames_per_led = []
        #for i in range(1, 9):
        #    frame = ttk.Frame(self.notebook)
        #    self.notebook.add(frame, text=f"LED {i} Viewer")
        #    self.viewer_frames_per_led.append(frame)
        #    self.draw_viewer_page_per_led(frame, i)

        self.notebook.add(self.calibration_frame, text="LCD Color Calibration")
        #self.notebook.add(self.csv_viewer_frame, text="CSV Viewer")
        #self.notebook.add(self.bin_viewer_frame, text="BIN Viewer")

        #self.draw_viewer_page(self.viewer_frame)
        self.create_calibration_interface(self.calibration_frame)
        self.refresh_com_ports()
        #self.draw_csv_viewer_page(self.csv_viewer_frame)
        #self.draw_bin_viewer_page(self.bin_viewer_frame)
        
        # === F1–F8 to switch to LED 1–8 Viewer tabs ===
        #for i in range(1, 9):
        #    self.root.bind_all(f"<F{i}>", lambda e, idx=i: self.switch_to_tab(idx))

        # === F9: Calibration tab, F10: CSV Viewer, F11: BIN Viewer ===
        self.root.bind_all("<F9>", lambda e: self.switch_to_tab(9))
        #self.root.bind_all("<F10>", lambda e: self.switch_to_tab(10))
        #self.root.bind_all("<F11>", lambda e: self.switch_to_tab(11))

        #for i in range(1, 9):
        #    self.root.bind_all(f"<Alt-Key-{i}>", lambda e, n=i: self.select_led_by_hotkey(n))

        #self.root.bind_all("<Control-Alt-l>", lambda event: self.load_rgb_from_csv())
        #self.root.bind_all("<Control-Alt-L>", lambda event: self.load_rgb_from_csv())

        self.root.bind_all("<Control-Alt-a>", lambda event: self.apply_rgb())
        self.root.bind_all("<Control-Alt-A>", lambda event: self.apply_rgb())

        self.root.bind_all("<Control-Alt-k>", lambda event: self.on_auto_cal_button_pressed())
        self.root.bind_all("<Control-Alt-K>", lambda event: self.on_auto_cal_button_pressed())

        self.root.bind_all("<Control-Alt-c>", lambda event: self.clear_points())
        self.root.bind_all("<Control-Alt-C>", lambda event: self.clear_points())

        self.fullscreen = False  # Track full-screen state
        self.root.bind_all("<F12>", self.toggle_fullscreen)
        self.root.bind_all("<Escape>", self.exit_fullscreen_or_go_home)

        #self.root.bind_all("<Left>", self.go_to_previous_tab)
        #self.root.bind_all("<Right>", self.go_to_next_tab)

        for color, key in self.color_hotkeys.items():
            self.root.bind_all(f"<Alt-{key}>", lambda e, c=color: self.select_color_by_hotkey(c))
            self.root.bind_all(f"<Alt-{key.upper()}>", lambda e, c=color: self.select_color_by_hotkey(c))

        for key in ['r', 'g', 'b', 'l']:
            self.root.bind_all(f"<Control-{key}>", lambda e, k=key: self.focus_rgb_entry(k))
            self.root.bind_all(f"<Control-{key.upper()}>", lambda e, k=key: self.focus_rgb_entry(k))
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "cie256x256.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen_or_go_home(self, event=None):
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes("-fullscreen", False)
        else:
            self.notebook.select(0)  # Switch to CIE1976 Viewer tab
    
    def go_to_previous_tab(self, event=None):
        current_index = self.notebook.index(self.notebook.select())
        if current_index > 0:
            self.switch_to_tab(current_index - 1)

    def go_to_next_tab(self, event=None):
        current_index = self.notebook.index(self.notebook.select())
        total_tabs = len(self.notebook.tabs())
        if current_index < total_tabs - 1:
            self.switch_to_tab(current_index + 1)

    def switch_to_tab(self, index):
        self.notebook.select(index)
        tab_name = self.notebook.tab(index, "text")
        self.root.title(f"CIE1976 Utility - {tab_name}")

    def add_logo_to_toolbar(self, toolbar):
        if not self.logo_photo:
            return
        
        logo_label = tk.Label(toolbar, image=self.logo_photo,
                          bg=toolbar.cget("bg"), borderwidth=0, highlightthickness=0)
        logo_label.image = self.logo_photo
        logo_label.place(relx=0.5, rely=0.5, anchor='center')

    def add_logo_to_frame(self, frame):
        if not self.logo_photo:
            return
        logo_label = tk.Label(frame, image=self.logo_photo, bg=frame.cget("bg"))
        logo_label.image = self.logo_photo
        logo_label.pack(side=tk.TOP, pady=5)

    def on_closing(self):
        self.root.destroy()
        sys.exit()

    def update_viewer_page_per_led(self, led_num):
        if 1 <= led_num <= len(self.viewer_frames_per_led):
            frame = self.viewer_frames_per_led[led_num - 1]

            for widget in frame.winfo_children():
                widget.destroy()

            self.draw_viewer_page_per_led(frame, led_num)

    def update_main_viewer_page(self):
        for widget in self.viewer_frame.winfo_children():
            widget.destroy()
        self.draw_viewer_page(self.viewer_frame)

    def draw_viewer_page_per_led(self, frame, led_num):
        fig, ax = plt.subplots(figsize=(7, 5))
        colour.plotting.colour_style()
        colour.plotting.plot_chromaticity_diagram_CIE1976UCS(show=False, axes=ax)
        ax.set_title(f"CIE 1976 Viewer - LED {led_num}")
        ax.set_xlim(0, 0.7)
        ax.set_ylim(0, 0.7)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)

        df_xlsx = pd.read_excel(self.xlsx_path, sheet_name="LED SPEC", header=None)
        ellipses = []
        for i in range(len(df_xlsx)):
            if "Target Coordinates" in str(df_xlsx.iat[i, 0]):
                try:
                    u, v = map(float, str(df_xlsx.iat[i + 1, 1]).split(','))
                    major = float(df_xlsx.iat[i + 2, 1]) * 2
                    minor = float(df_xlsx.iat[i + 3, 1]) * 2
                    angle = float(df_xlsx.iat[i + 4, 1])
                    ellipse = Ellipse((u, v), major, minor, angle=angle, edgecolor='black', facecolor='none', linewidth=0.5)
                    ax.add_patch(ellipse)
                    ellipses.append((u, v, major, minor, angle))
                except:
                    pass

        if os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path)
            df_led = df[df['LED'] == led_num]
            u_values = df_led["u`"].values
            v_values = df_led["v`"].values

            pass_x, pass_y, fail_x, fail_y = [], [], [], []
            for x, y in zip(u_values, v_values):
                if any(self.is_point_in_ellipse(x, y, u, v, major, minor, angle) for (u, v, major, minor, angle) in ellipses):
                    pass_x.append(x)
                    pass_y.append(y)
                else:
                    fail_x.append(x)
                    fail_y.append(y)

            ax.scatter(pass_x, pass_y, color='green', s=20, alpha=0.7, label="PASS")
            ax.scatter(fail_x, fail_y, color='red', s=20, alpha=0.7, label="FAIL")

        ax.legend(loc='upper right', fontsize=9)
        fig = plt.gcf()
        plugins.connect(fig, TickStylePlugin())

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.add_logo_to_toolbar(toolbar)

    def draw_viewer_page(self, frame):
        fig, ax = plt.subplots(figsize=(7, 5))
        colour.plotting.colour_style()
        colour.plotting.plot_chromaticity_diagram_CIE1976UCS(show=False, axes=ax)
        ax.set_title("CIE 1976 Viewer")
        ax.set_xlim(0, 0.7)
        ax.set_ylim(0, 0.7)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)

        df_xlsx = pd.read_excel(self.xlsx_path, sheet_name="LCD SPEC", header=None)
        ellipses = []
        label_added = False
        for i in range(len(df_xlsx)):
            if "Target Coordinates" in str(df_xlsx.iat[i, 0]):
                try:
                    u, v = map(float, str(df_xlsx.iat[i + 1, 1]).split(','))
                    major = float(df_xlsx.iat[i + 2, 1]) * 2
                    minor = float(df_xlsx.iat[i + 3, 1]) * 2
                    angle = float(df_xlsx.iat[i + 4, 1])
                    label = os.path.basename(self.xlsx_path) if not label_added else None
                    ellipse = Ellipse((u, v), major, minor, angle=angle,
                                      edgecolor='black', facecolor='none', linewidth=0.5, label=label)
                    ax.add_patch(ellipse)
                    ellipses.append((u, v, major, minor, angle))
                    label_added = True
                except:
                    pass

        if os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path)
            #df_csv.columns = df_csv.columns.str.strip().str.replace("’", "'", regex=False)
            u_values = df["u`"].values
            v_values = df["v`"].values

            if "target u`" in df.columns and "target v`" in df.columns:
               target_u_values = df["target u`"].dropna().values
               target_v_values = df["target v`"].dropna().values
               ax.scatter(target_u_values, target_v_values, color='black', s=20, alpha=0.8, label="TARGET")
            else:
               target_u_values = []
               target_v_values = []
               print("Missing 'target u`' or 'target v`' columns in CSV.")

            pass_x, pass_y, fail_x, fail_y = [], [], [], []
            results = []
            for x, y in zip(u_values, v_values):
                if any(self.is_point_in_ellipse(x, y, u, v, major, minor, angle) for (u, v, major, minor, angle) in ellipses):
                    pass_x.append(x)
                    pass_y.append(y)
                    results.append("PASS")
                else:
                    fail_x.append(x)
                    fail_y.append(y)
                    results.append("FAIL")

            df["Result"] = results
            result_path = os.path.splitext(self.csv_path)[0] + "_result.csv"
            df.to_csv(result_path, index=False)
            ax.scatter(pass_x, pass_y, color='green', s=20, alpha=0.7, label="PASS")
            ax.scatter(fail_x, fail_y, color='red', s=20, alpha=0.7, label="FAIL")

        # === Define legend ===
        def make_ellipse_legend(legend, orig_handle, xdescent, ydescent, width, height, fontsize):
            return Ellipse((width / 2, height / 2), width=10, height=5, edgecolor='black', facecolor='none', linewidth=1)

        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=9,
                  handler_map={Ellipse: HandlerPatch(patch_func=make_ellipse_legend)})
        
        # === Add live cursor coordinates plugin ===
        fig = plt.gcf()
        plugins.connect(fig, MousePositionPlugin())
        plugins.connect(fig, TickStylePlugin())
        #plugins.connect(fig, CrosshairPlugin())

        # === Save HTML ===
        html_path = 'cie1976_out.html'
        with open(html_path, "w", encoding="utf-8") as f:
             f.write(mpld3.fig_to_html(fig))

        viewer_canvas = FigureCanvasTkAgg(fig, master=frame)
        viewer_canvas.draw()
        viewer_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(viewer_canvas, frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.add_logo_to_toolbar(toolbar)

    def create_calibration_interface(self, frame):
        #self.led_radiobuttons = {}
        self.lens_radiobuttons = {}
        self.color_radiobuttons = {}
        self.rgb_entries = {}

        container = ttk.Frame(frame)
        container.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        colour.plotting.plot_chromaticity_diagram_CIE1931(show=False, axes=self.ax)
        self.ax.set_title("LCD Calibration - CIE 1931")
        self.ax.set_xlim(0.0, 0.8)
        self.ax.set_ylim(0.0, 0.9)
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)

        df = pd.read_excel(self.xlsx_path, sheet_name="LCD SPEC", header=None)
        self.ellipses = []
        for i in range(len(df)):
            if "Target Coordinates" in str(df.iat[i, 0]):
                try:
                    x, y = map(float, str(df.iat[i + 1, 1]).split(','))
                    major = float(df.iat[i + 2, 1]) * 2
                    minor = float(df.iat[i + 3, 1]) * 2
                    angle = float(df.iat[i + 4, 1])
                    e = Ellipse((x, y), major, minor, angle=angle, edgecolor='black', facecolor='none', linewidth=0.5)
                    self.ax.add_patch(e)
                    self.ellipses.append(e)
                except:
                    pass

        canvas_container = ttk.Frame(container)
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, canvas_container)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.add_logo_to_toolbar(toolbar)

        control_frame = ttk.Frame(container, padding=10)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(control_frame, text="Cover Lens:").pack(anchor=tk.W, pady=(10, 0))
        for lens in self.cover_lenses:
            rb = tk.Radiobutton(
                control_frame,
                text=lens,
                variable=self.selected_cover_lens,
                value=lens,
                width=10,
                anchor="w",
                font=("Arial", 10),
                foreground="#000000",
                background="#f0f0f0",
                activeforeground="#0044cc",
                activebackground="#d0e4ff",
                selectcolor="#ffffff",
                #underline=underline_index,
                command=self.on_cover_lens_selected
            )
            rb.pack(anchor=tk.W)
            self.lens_radiobuttons[lens.lower()] = rb

        ttk.Label(control_frame, text="Select Color:").pack(anchor=tk.W, pady=(10, 0))
        for color in self.colors:
            key = self.color_hotkeys.get(color, "")
            underline_index = color.lower().find(key) if key else -1
            rb = tk.Radiobutton(
                control_frame,
                text=color,
                variable=self.selected_color,
                value=color,
                width=5,
                anchor="w",
                font=("Arial", 10),
                foreground="#000000",
                background="#f0f0f0",
                activeforeground="#0044cc",
                activebackground="#d0e4ff",
                selectcolor="#ffffff",
                underline=underline_index,
                command=self.on_color_selected   # Add command to handle selection
            )
            rb.pack(anchor=tk.W)
            self.color_radiobuttons[color.lower()] = rb

        # Select "White" by default
        self.selected_color.set("White")
        self.on_color_selected()

        self.r_value = tk.StringVar(value="255")  # default to max
        self.g_value = tk.StringVar(value="255")  # default to max
        self.b_value = tk.StringVar(value="255")  # default to max
        self.brightness_value = tk.StringVar(value="100")  # default to max
        self.com_var = tk.StringVar()

        ttk.Label(control_frame, text="Red:").pack(anchor=tk.W, pady=(10, 0))
        r_entry = ttk.Entry(control_frame, textvariable=self.r_value, width=10)
        r_entry.pack(anchor=tk.W)
        self.rgb_entries["r"] = r_entry
        ToolTip(r_entry, text="Red intensity (0–255)\nShortcut: Ctrl+R")

        ttk.Label(control_frame, text="Green:").pack(anchor=tk.W)
        g_entry = ttk.Entry(control_frame, textvariable=self.g_value, width=10)
        g_entry.pack(anchor=tk.W)
        self.rgb_entries["g"] = g_entry
        ToolTip(g_entry, text="Green intensity (0–255)\nShortcut: Ctrl+G")

        ttk.Label(control_frame, text="Blue:").pack(anchor=tk.W)
        b_entry = ttk.Entry(control_frame, textvariable=self.b_value, width=10)
        b_entry.pack(anchor=tk.W)
        self.rgb_entries["b"] = b_entry
        ToolTip(b_entry, text="Blue intensity (0–255)\nShortcut: Ctrl+B")

        ttk.Label(control_frame, text="Brightness: 0 ~ 100%").pack(anchor=tk.W, pady=(10, 0))
        brightness_entry = ttk.Entry(control_frame, textvariable=self.brightness_value, width=10)
        brightness_entry.pack(anchor=tk.W)
        self.rgb_entries["l"] = brightness_entry
        ToolTip(brightness_entry, text="Brightness level (0–100%)")

        ttk.Label(control_frame, text="Serial Port:").pack(anchor=tk.W, pady=(10, 0))
        self.com_combo = ttk.Combobox(control_frame, textvariable=self.com_var, state="readonly", width=15)
        self.com_combo.pack(anchor="w", pady=2)

        #self.source_option = tk.StringVar(value="CL200A")  # Default to CL200A
        self.source_option = tk.StringVar(value="CS-160")  # Default to CS-160

        ttk.Label(control_frame, text="Measurement Source:").pack(anchor=tk.W, pady=(10, 0))
        ttk.Combobox(
            control_frame,
            textvariable=self.source_option,
            values=["CL200A", "CS-160"],
            state="readonly"
        ).pack(anchor=tk.W)

        #load_btn = ttk.Button(control_frame, text="Load", underline=0, takefocus=False, command=self.load_rgb_from_csv)
        #load_btn.pack(anchor=tk.CENTER, pady=5)
        #ToolTip(load_btn, text="Load RGB data for the selected LED and color (Ctrl+Alt+L)")

        apply_btn = ttk.Button(control_frame, text="Apply", underline=0, takefocus=False, command=self.apply_rgb)
        apply_btn.pack(anchor=tk.CENTER, pady=10)
        ToolTip(apply_btn, text="Apply current RGB and brightness to the LED and run check (Ctrl+Alt+A)")

        auto_btn = ttk.Button(control_frame, text="Auto CAL", takefocus=False, command=self.on_auto_cal_button_pressed)
        auto_btn.pack(anchor=tk.CENTER, pady=10)
        ToolTip(auto_btn, text="Auto calibrate all 8 colors in sequence (Ctrl+Alt+K)")

        clear_btn = ttk.Button(control_frame, text="Clear", underline=0, takefocus=False, command=self.clear_points)
        clear_btn.pack(anchor=tk.CENTER, pady=5)
        ToolTip(clear_btn, text="Clear all points and results, and delete calibration files (Ctrl+Alt+C)")

        self.coord_label = ttk.Label(control_frame, text="x = ---, y = ---", padding=5)
        self.coord_label.pack(anchor=tk.CENTER, pady=(10, 0))

    def compute_correction_matrix(self, csv_path, target_lens):
        """
        Solve: C_ideal * A ≈ C_meas
        Return: 3x3 correction matrix A
        """
        if not os.path.exists(csv_path):
            print(f"Error: {csv_path} not found.")
            return np.eye(3)
        
        # 1. Read measured data
        df = pd.read_csv(csv_path)

        C_ideal = []
        C_meas = []
        color_list = [] 

        # filtered Cover Lens
        df_filtered = df[df["Cover Lens"] == target_lens]

        for _, row in df_filtered.iterrows():
            color = row["Color"]

            # Skip unknown colors
            if color not in self.color_rgb_map:
                continue

            C_ideal.append(self.color_rgb_map[color])
            C_meas.append([row["R"], row["G"], row["B"]])
            color_list.append(color)

        C_ideal = np.array(C_ideal, dtype=np.float64)
        C_meas  = np.array(C_meas,  dtype=np.float64)
        
        gamma = 2.2
        C_ideal_linear = np.power(C_ideal / 255.0, gamma)
        C_meas_linear  = np.power(C_meas / 255.0, gamma)

        #if C_ideal.shape[0] < 4:
        if C_ideal.shape[0] < 3:
            raise ValueError("Not enough color samples to solve correction matrix")

        #ones = np.ones((C_ideal.shape[0], 1))
        #C_ideal_ext = np.hstack([C_ideal, ones])

        # 2. Least squares solve
        #A, residuals, rank, s = np.linalg.lstsq(C_ideal_ext, C_meas, rcond=None)
        #A, residuals, rank, s = np.linalg.lstsq(C_ideal, C_meas, rcond=None)
        A, residuals, rank, s = np.linalg.lstsq(C_ideal_linear, C_meas_linear, rcond=None)
 
        print("\n=== Calibration Input Matrices ===")
        print("\nColors order:")
        for i, c in enumerate(color_list):
            print(f"{i:2d}: {c}")

        print("\nC_ideal (Nx3):")
        print(C_ideal)
        print("\nC_meas (Nx3):")
        print(C_meas)

        print("=== RGB Correction Matrix ===")
        print(A)
        print("Residuals:", residuals)
        print("Rank:", rank)

        self.correction_matrix = A
        return A

    def refresh_com_ports(self):
        ports = detect_com_ports()
        self.com_combo["values"] = ports

        if ports:
            self.com_combo.current(0)
        else:
            self.com_combo.set("No COM Port")

    def on_cover_lens_selected(self):
        lens = self.selected_cover_lens.get()
        print(f"[INFO] Cover lens selected: {lens}")

    def on_color_selected(self):
        color = self.selected_color.get()
        if color not in self.color_rgb_map:
            return

        r, g, b = self.color_rgb_map[color]

        self.r_value.set(str(r))
        self.g_value.set(str(g))
        self.b_value.set(str(b))

    def select_led_by_hotkey(self, led_num):
        self.selected_led.set(led_num)
        if hasattr(self, "led_radiobuttons") and led_num in self.led_radiobuttons:
            self.led_radiobuttons[led_num].focus_set()

    def select_color_by_hotkey(self, color_name):
        if color_name not in self.color_rgb_map:
            return
    
        self.selected_color.set(color_name)

        r, g, b = self.color_rgb_map[color_name]
        self.r_value.set(str(r))
        self.g_value.set(str(g))
        self.b_value.set(str(b))

        rb = self.color_radiobuttons.get(color_name.lower())
        if rb:
            rb.focus_set()

    def focus_rgb_entry(self, key):
        entry = self.rgb_entries.get(key.lower())
        if entry:
            entry.focus_set()
            entry.select_range(0, tk.END)

    def draw_csv_viewer_page(self, frame):
        columns = ["Timestamp", "LED", "Color", "R", "G", "B", "Brightness", "u`", "v`", "X", "Y", "Z"]

        container = ttk.Frame(frame)
        container.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(container, columns=columns, show="headings")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor=tk.CENTER)

        self.load_calibrated_csv()
        self.refresh_csv_viewer()

        logo_frame = tk.Frame(frame, height=46, bg="#e0e0e0")
        logo_frame.pack(fill=tk.X, side=tk.BOTTOM)
        logo_frame.pack_propagate(False)
        self.add_logo_to_frame(logo_frame)

    def load_calibrated_csv(self):
        if not os.path.exists(self.calibrated_path):
            if not os.path.exists(self.csv_path):
                messagebox.showerror("Error", f"Source file not found: {self.csv_path}")
                return
        
            try:
                df_src = pd.read_csv(self.csv_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read source CSV: {e}")
                return

            # Expected columns
            expected_cols = ["LED", "Color", "R", "G", "B", "Brightness", "u`", "v`", "X", "Y", "Z"]
            for col in expected_cols:
                if col not in df_src.columns:
                    df_src[col] = 0

            df_src = df_src[expected_cols].fillna(0)
            df_src.insert(0, "Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Reorder by LED (1–8) and Color (Green, Blue, Yellow, Orange, White, Purple)
            df_src["Color"] = pd.Categorical(df_src["Color"], categories=self.colors, ordered=True)
            df_src.sort_values(by=["LED", "Color"], inplace=True)

            df_src.to_csv(self.calibrated_path, index=False)
            print("calibrated.csv created.")

    def load_rgb_from_csv(self):
        if not os.path.exists(self.csv_path):
            messagebox.showerror("Error", f"{self.csv_path} not found.")
            return

        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV: {e}")
            return

        led = self.selected_led.get()
        color = self.selected_color.get()

        match = df[(df["LED"] == led) & (df["Color"].str.lower() == color.lower())]

        if not match.empty:
            row = match.iloc[0]
            r = int(row.get("R", 0))
            g = int(row.get("G", 0))
            b = int(row.get("B", 0))
            u = float(row.get("u`", 0))
            v = float(row.get("v`", 0))
        else:
            r = g = b = 0
            u = v = 0.0

        self.r_value.set(str(r))
        self.g_value.set(str(g))
        self.b_value.set(str(b))
        self.coord_label.config(text=f"u′ = {u:.4f}, v′ = {v:.4f}")

        self.load_calibrated_csv()
        self.refresh_csv_viewer()

    def apply_rgb(self):
        self.clear_pass_fail_points()
        self.root.after(9000, self.delayed_check_uv_csv)
        try:
             r_orig = int(self.r_value.get())
             g_orig = int(self.g_value.get())
             b_orig = int(self.b_value.get())
             brightness = int(self.brightness_value.get())
             current_lens = self.selected_cover_lens.get()
             if current_lens in ["WarmGold", "black", "silver"]:
                print(f"Applying correction for {current_lens}...")
                correction_matrix = self.compute_correction_matrix(self.calibrated_path, current_lens)
                #original_rgb = np.array([r_orig, g_orig, b_orig], dtype=np.float64)
                #corrected_rgb = original_rgb @ correction_matrix
                #A_ext = self.compute_correction_matrix(self.calibrated_path, current_lens)
                #input_vec = np.array([r_orig, g_orig, b_orig, 1.0])
                #corrected_rgb = input_vec @ A_ext
                gamma = 2.2
                inv_gamma = 1.0 / gamma
                in_linear = np.power(np.array([r_orig, g_orig, b_orig]) / 255.0, gamma)
                out_linear = in_linear @ correction_matrix
                rgb_max = 1.0
                corrected_rgb = np.power(out_linear, inv_gamma) * (255.0 / rgb_max)

                r = int(np.clip(corrected_rgb[0], 0, 255))
                g = int(np.clip(corrected_rgb[1], 0, 255))
                b = int(np.clip(corrected_rgb[2], 0, 255))
                #r, g, b = r_orig, g_orig, b_orig
                print(f"Corrected RGB: {r}, {g}, {b}")
                matrix_flattened = correction_matrix.flatten()
                matrix_string = ",".join([f"{x:.8f}" for x in matrix_flattened])
                print(f"disp_cal_mf: {matrix_string}")
                print(f"disp_cal_rgb_max: {rgb_max}")
             else:
                r, g, b = r_orig, g_orig, b_orig
        except ValueError:
            print("Invalid RGB input")
            return

        if not (0 <= brightness <= 255):
           print("Brightness must be between 0 and 255.")
           return

        self.refresh_com_ports()
        selected_port = self.com_var.get()
        if not selected_port or "No COM" in selected_port:
           messagebox.showerror("Error", "Please select COM port")
           return

        _uart.port = selected_port

        system = platform.system()
    
        if system == "Windows":
            if enable_lcd:
                success = enable_lcd(r, g, b, brightness)
                if success:
                    print(f"[OK] Enabled LCD with RGB={r,g,b}, brightness={brightness}")
                else:
                    print("[FAIL] Could not control LCD.")
            else:
               print("[WARN] LCD control not available (import failed).")

            if self.source_option.get() == "CL200A":
                # Define the executable path (CL200A)
                exe_path = os.path.join("CL200AOneShot", "CL200aOneShotMeasurement.exe")
            else:
                # Define the executable path (CS-160)
                exe_path = os.path.join("CS160OneShot", "OneShotMeasurementTool.exe")

            # Launch the executable
            try:
                print(f"Launching: {exe_path}")
                subprocess.Popen(exe_path, shell=True)
                print("Executable launched successfully.")
            except Exception as e:
                print(f"Failed to launch {exe_path}: {e}")
        elif system == "Linux":
              """
              dev = self.find_ch341_i2c_device()
              if dev:
                     print(f"Using CH341 I2C device: {dev}")
                     set_led_color_ch341(r, g, b, brightness, led_list)
              else:
                  print("CH341 I2C device not available or unsupported platform.")
              """
        else:
            print(f"[WARNING] Unsupported platform: {system}")
            return
        """
        # Compute chromaticity for plotting
        r_lin = r / 255.0
        g_lin = g / 255.0
        b_lin = b / 255.0

        x = 0.4124 * r_lin + 0.3576 * g_lin + 0.1805 * b_lin
        y = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
        z = 0.0193 * r_lin + 0.1192 * g_lin + 0.9505 * b_lin

        denom = x + 15 * y + 3 * z

        if denom == 0:
            print("Chromaticity calculation skipped due to zero denominator (black color).")
            return

        u_prime = (4 * x) / denom
        v_prime = (9 * y) / denom

        point = self.ax.scatter([u_prime], [v_prime], color='black', s=30, zorder=5)
        label = self.ax.text(u_prime + 0.005, v_prime + 0.005, str(self.point_counter), fontsize=8, color='black')
        self.plotted_points.append(point)
        self.plotted_labels.append(label)
        self.point_counter += 1

        self.coord_label.config(text=f"u′ = {u_prime:.4f}, v′ = {v_prime:.4f}")
        self.canvas.draw()
        """

    def find_ch341_i2c_device(self):
        i2c_base = "/sys/class/i2c-adapter"
        ch341_id = "1a86/5512"  # CH341 USB Vendor/Product ID

        for adapter in os.listdir(i2c_base):
            adapter_path = os.path.join(i2c_base, adapter)
            device_symlink = os.path.join(adapter_path, "device")
            if not os.path.islink(device_symlink):
                continue

            try:
                real_device_path = os.path.realpath(device_symlink)
                uevent_file = os.path.join(real_device_path, "uevent")
                if os.path.exists(uevent_file):
                    with open(uevent_file, 'r') as f:
                        uevent = f.read()
                        if ch341_id in uevent:
                            return f"/dev/{adapter}"  # e.g., /dev/i2c-18
            except Exception:
                continue

        return None

    def xyz_to_xy(self, X, Y, Z):
        denom = X + Y + Z
        if denom == 0:
            return None, None
        x = X / denom
        y = Y / denom
        return x, y

    def get_color_set_rgb_val(self):
        color = self.selected_color.get()
        if color not in self.color_rgb_map:
            return
        
        r, g, b = self.color_rgb_map[color]
        self.r_value.set(str(r))
        self.g_value.set(str(g))
        self.b_value.set(str(b))

    def delayed_check_uv_csv(self):
        measured_csv = "measured.csv"
        file_exists = os.path.exists(measured_csv)
        measured_f = open(measured_csv, "a", newline="", encoding="utf-8")
        measured_writer = csv.writer(measured_f)

        if not file_exists:
            measured_writer.writerow([
                "TimeStamp", "Color",
                "R", "G", "B",
                "x", "y",
                "u`", "v`",
                "X", "Y", "Z"
            ])

        if self.source_option.get() == "CL200A":
            file_path = self.cl200a_path
        else:
            file_path = self.cs160_path

        if not os.path.exists(file_path):
            messagebox.showerror("File Not Found", f"{file_path} not found.")
            return

        with open(file_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            """
            # Overwrite u'v' in data_dut_pwm_uv.csv
            df_main = pd.read_csv(self.csv_path)
            df_main.columns = df_main.columns.str.strip().str.replace("’", "`", regex=False).str.replace("'", "`", regex=False)
            
            r0 = int(self.r_value.get())
            g0 = int(self.g_value.get())
            b0 = int(self.b_value.get())
            """

            for row in reader:
                try:
                    u = float(row["u`"])
                    v = float(row["v`"])
                    X = float(row["X"])
                    Y = float(row["Y"])
                    Z = float(row["Z"])
                except (KeyError, ValueError):
                    continue

                x, y = self.xyz_to_xy(X, Y, Z)
                if x is None:
                    continue

                color_name = self.selected_color.get()
                cx_target, cy_target = self.ellipse_centers.get(color_name, (None, None))

                timestamp = datetime.now().isoformat(timespec="seconds")
                r0 = int(self.r_value.get())
                g0 = int(self.g_value.get())
                b0 = int(self.b_value.get())

                measured_writer.writerow([
                    timestamp, color_name,
                    r0, g0, b0,
                    round(x, 6), round(y, 6),
                    round(u, 6), round(v, 6),
                    round(X, 6), round(Y, 6), round(Z, 6)
                ])

                """
                try:
                    u = float(row["u`"])
                    v = float(row["v`"])
                except (ValueError, KeyError):
                    continue  # skip invalid or missing data

                led_number = self.selected_led.get()
                color_name = self.selected_color.get()
                cx_target, cy_target = self.ellipse_centers.get(color_name, (None, None))
                #print(f"CS-160 data: {color_name}")

                mask = (df_main["LED"] == led_number) & (df_main["Color"] == color_name)
                df_main.loc[mask, "u`"] = u
                df_main.loc[mask, "v`"] = v
                df_main.loc[mask, "R"] = r0
                df_main.loc[mask, "G"] = g0
                df_main.loc[mask, "B"] = b0
                """

                result = "FAIL"

                """
                for e in self.ellipses:
                    cx, cy = e.center
                    major, minor, angle = e.width, e.height, e.angle
                    if self.is_point_in_ellipse(u, v, cx, cy, major, minor, angle):
                        result = "PASS"
                        self.save_calibration()
                        self.save_bin_file()
                        break
                """
                if cx_target is not None and cy_target is not None:
                    for e in self.ellipses:
                        cx, cy = e.center
                        major, minor, angle = e.width, e.height, e.angle
                        if cx == cx_target and cy == cy_target:
                            if self.is_point_in_ellipse(x, y, cx, cy, major, minor, angle):
                                result = "PASS"
                                break

                self.plot_pass_fail_point(x, y, result)

                print(f"x={x:.5f}, y={y:.5f}, Result={result}")

                if result == "FAIL":
                    cx, cy = self.ellipse_centers.get(color_name, (None, None))
                    if cx is None or cy is None:
                        print(f"Warning: Could not find ellipse center for color '{color_name}'")
                        continue

                    dx = cx - x
                    dy = cy - y
                    print(f"Δx={dx:.5f}, Δy={dy:.5f}")

                    #delta_u = cx - u
                    #delta_v = cy - v

                    #r1, g1, b1 = adjust_u_prime_percentage(r0, g0, b0, delta_u)
                    #r2, g2, b2 = adjust_v_prime_percentage(r1, g1, b1, delta_v)

                    #print(f"delta_u: {delta_u:.5f}, delta_v: {delta_v:.5f}")
                    #print(f"R: {r0} → {r1:.1f}, G: {g0} → {g1:.1f}, B: {b0} → {b1:.1f}")
                    #print(f"R: {r1} → {r2:.1f}, G: {g1} → {g2:.1f}, B: {b1} → {b2:.1f}")

                    #r_suggest = int(np.clip(round(r2), 0, 255))
                    #g_suggest = int(np.clip(round(g2), 0, 255))
                    #b_suggest = int(np.clip(round(b2), 0, 255))

                    #msg = f"""The measured result did not fall within the tolerance ellipse.
                    #Suggested RGB adjustment:
                    #R: {r0} → {r_suggest}
                    #G: {g0} → {g_suggest}
                    #B: {b0} → {b_suggest}

                    #Ellipse center: ({cx:.4f}, {cy:.4f})
                    #Measured u′: {u:.4f}, v′: {v:.4f}
                    #Delta u′: {delta_u:.4f}, Delta v′: {delta_v:.4f}

                    #Please manually update the values and press Apply again"""
                    #messagebox.showinfo("Suggested RGB Adjustment", msg)

            # Save changes to CSV
            #if result == "PASS":
            """
            df_main.to_csv(self.csv_path, index=False)

            self.update_viewer_page_per_led(self.selected_led.get())
            self.update_main_viewer_page()
            """
        measured_f.close()

        if os.path.exists(file_path):
           os.remove(file_path)

    def on_auto_cal_button_pressed(self):
        self.clear_pass_fail_points()
        self.auto_retry_count = 0
        self.auto_color_index = 0
        #self.auto_color_index = 5  # Start from White for testing
        self.auto_color_list = self.colors.copy()
        self.selected_color.set(self.auto_color_list[self.auto_color_index])
        self.auto_init_pid()
        #self.load_rgb_from_csv()
        self.auto_apply_rgb()

    def auto_apply_rgb(self):
        try:
            r = int(self.r_value.get())
            g = int(self.g_value.get())
            b = int(self.b_value.get())
            brightness = int(self.brightness_value.get())
        except ValueError:
            messagebox.showerror("Input Error", "Invalid RGB input.")
            return

        if not (0 <= brightness <= 100):
            messagebox.showerror("Input Error", "Brightness must be between 0 and 100.")
            return

        self.refresh_com_ports()
        selected_port = self.com_var.get()
        if not selected_port or "No COM" in selected_port:
           messagebox.showerror("Error", "Please select COM port")
           return

        _uart.port = selected_port

        if enable_lcd:
            success = enable_lcd(r, g, b, brightness)
            if success:
                print(f"[OK] Enabled LCD with RGB={r,g,b}, brightness={brightness}")
            else:
                print("[FAIL] Could not control LCD.")
        else:
           print("[WARN] LCD control not available (import failed).")

        # Define the executable path (CL200A)
        #exe_path = os.path.join("CL200AOneShot", "CL200aOneShotMeasurement.exe")
        # Define the executable path (CS-160)
        exe_path = os.path.join("CS160OneShot", "OneShotMeasurementTool.exe")

        try:
            print(f"Launching: {exe_path}")
            subprocess.Popen(exe_path, shell=True)
        except Exception as e:
            print(f"Failed to launch {exe_path}: {e}")

        self.root.after(9000, self.auto_delayed_check_csv_uv)
    
    def auto_delayed_check_csv_uv(self):
        #file_path = self.cl200a_path
        file_path = self.cs160_path

        if not os.path.exists(file_path):
            messagebox.showerror("File Not Found", f"{file_path} not found.")
            return

        with open(file_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            #df_main = pd.read_csv(self.csv_path)
            #df_main.columns = df_main.columns.str.strip().str.replace("’", "`", regex=False).str.replace("'", "`", regex=False)

            r0 = int(self.r_value.get())
            g0 = int(self.g_value.get())
            b0 = int(self.b_value.get())

            for row in reader:
                try:
                    X = float(row["X"])
                    Y = float(row["Y"])
                    Z = float(row["Z"])
                except (KeyError, ValueError):
                    continue

                x, y = self.xyz_to_xy(X, Y, Z)
                if x is None:
                    continue

        color_name = self.selected_color.get()
        cx_target, cy_target = self.ellipse_centers.get(color_name, (None, None))
        result = "FAIL"

        if cx_target is not None and cy_target is not None:
            for e in self.ellipses:
                cx, cy = e.center
                major, minor, angle = e.width, e.height, e.angle
                if cx == cx_target and cy == cy_target:
                    if self.is_point_in_ellipse(x, y, cx, cy, major, minor, angle):
                        self.save_calibration()
                        result = "PASS"
                        break

        self.plot_pass_fail_point(x, y, result)

        if result == "PASS":
            #if self.auto_color_index < len(self.auto_color_list) - 1:
            if self.auto_color_index < len(self.auto_color_list) - 3:
                self.auto_color_index += 1
                self.selected_color.set(self.auto_color_list[self.auto_color_index])
                
                color = self.selected_color.get()
                if color not in self.color_rgb_map:
                    return
        
                r, g, b = self.color_rgb_map[color]
                self.r_value.set(str(r))
                self.g_value.set(str(g))
                self.b_value.set(str(b))

                self.auto_retry_count = 0
                self.auto_init_pid()
                self.root.after(1000, self.auto_apply_rgb)
            else:
                messagebox.showinfo("Success", "Auto calibration completed for all colors.")
            #messagebox.showinfo("Success", "Auto calibration completed for the color.")
            return

        # If FAIL, then perform automatic correction
        cx, cy = self.ellipse_centers.get(color_name, (None, None))
        if cx is None or cy is None:
            print(f"Warning: No ellipse center found for color '{color_name}'")
            return

        delta_x = cx - x
        delta_y = cy - y

        #r1, g1, b1 = adjust_u_prime_percentage(r0, g0, b0, delta_u)
        #r2, g2, b2 = adjust_v_prime_percentage(r1, g1, b1, delta_v)
        #print(f"delta_u: {delta_u:.5f}, delta_v: {delta_v:.5f}")
        #print(f"R: {r0} → {r1:.1f}, G: {g0} → {g1:.1f}, B: {b0} → {b1:.1f}")
        #print(f"R: {r1} → {r2:.1f}, G: {g1} → {g2:.1f}, B: {b1} → {b2:.1f}")

        r1 = r0 + self.pid_x_r.compute(delta_x) * r0
        g1 = g0 + self.pid_x_g.compute(-delta_x) * g0
        b1 = b0 + self.pid_x_b.compute(-delta_x) * b0

        r2 = r1 + self.pid_y_r.compute(-delta_y) * r1
        g2 = g1 + self.pid_y_g.compute(delta_y) * g1
        b2 = b1 + self.pid_y_b.compute(-delta_y) * b1

        print(f"[Auto Correction] Δx={delta_x:.5f}, Δy={delta_y:.5f}")
        print(f"R: {r0} → {r1:.1f}, G: {g0} → {g1:.1f}, B: {b0} → {b1:.1f}")
        print(f"R: {r1} → {r2:.1f}, G: {g1} → {g2:.1f}, B: {b1} → {b2:.1f}")
        print(f"Suggested RGB: R={r2:.1f}, G={g2:.1f}, B={b2:.1f}")

        r_suggest = int(np.clip(round(r2), 0, 255))
        g_suggest = int(np.clip(round(g2), 0, 255))
        b_suggest = int(np.clip(round(b2), 0, 255))

        print(f"[Auto Correction] Suggested RGB: R={r_suggest}, G={g_suggest}, B={b_suggest}")

        # Increase retry count
        self.auto_retry_count += 1
        if self.auto_retry_count > 5:
            messagebox.showerror("Auto Calibration Failed", "Maximum retries (5) exceeded. Please adjust manually.")
            return

        # Update RGB entry fields with new suggested values
        self.r_value.set(r_suggest)
        self.g_value.set(g_suggest)
        self.b_value.set(b_suggest)

        # Wait 1 second before applying new RGB and starting next auto cycle
        self.root.after(1000, self.auto_apply_rgb)

        # Remove measurement file to force next cycle to generate fresh data
        if os.path.exists(file_path):
           os.remove(file_path)

    def auto_init_pid(self):
        """
        # PID controllers for u′
        self.pid_u_r = PIDController(kp=1.0, ki=1.0, kd=1.0)
        self.pid_u_g = PIDController(kp=3.0, ki=3.0, kd=3.0)
        self.pid_u_b = PIDController(kp=3.0, ki=5.0, kd=5.0)
        # PID controllers for v′
        self.pid_v_r = PIDController(kp=1.0, ki=1.0, kd=1.0)
        self.pid_v_g = PIDController(kp=3.0, ki=3.0, kd=3.0)
        self.pid_v_b = PIDController(kp=3.0, ki=5.0, kd=5.0)
        """
        # PID controllers for x
        self.pid_x_r = PIDController(kp=1.0, ki=2.0, kd=2.0)
        self.pid_x_g = PIDController(kp=0.9, ki=0.9, kd=0.8)
        self.pid_x_b = PIDController(kp=0.1, ki=0.1, kd=0.1)
        # PID controllers for y
        self.pid_y_r = PIDController(kp=1.0, ki=1.0, kd=1.0)
        self.pid_y_g = PIDController(kp=0.9, ki=0.9, kd=0.8)
        self.pid_y_b = PIDController(kp=0.1, ki=0.1, kd=0.1)
        
    def is_point_in_ellipse(self, x, y, cx, cy, major, minor, angle_deg):
        angle = np.radians(angle_deg)
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        dx, dy = x - cx, y - cy
        x_rot = dx * cos_a + dy * sin_a
        y_rot = -dx * sin_a + dy * cos_a
        return (x_rot / (major / 2))**2 + (y_rot / (minor / 2))**2 <= 1
    
    def save_calibration(self):
        u_prime, v_prime, X, Y, Z = "", "", "", "", ""
        try:
            if self.source_option.get() == "CL200A":
                cs160_df = pd.read_csv(self.cl200a_path, encoding='utf-8-sig')
            else:
                cs160_df = pd.read_csv(self.cs160_path, encoding='utf-8-sig')
            if not cs160_df.empty:
                row = cs160_df.iloc[0]
                u_prime = row["u`"]
                v_prime = row["v`"]
                X = row["X"]
                Y = row["Y"]
                Z = row["Z"]
        except Exception as e:
            print(f"Warning: could not append CS-160 data: {e}")
    
        try:
            r = int(self.r_value.get())
            g = int(self.g_value.get())
            b = int(self.b_value.get())
            brightness = int(self.brightness_value.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid R, G, B or Brightness value.")
            return

        lens_name = self.selected_cover_lens.get()
        color_name = self.selected_color.get()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Only create calibrated.csv if it doesn't exist
        #if not os.path.exists(self.calibrated_path):
        #    self.load_calibrated_csv()

        updated_rows = []
        found = False

        # Read existing rows (if file exists)
        if os.path.exists(self.calibrated_path):
            with open(self.calibrated_path, mode='r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader)
                for row in reader:
                    if str(lens_name) == row[1] and color_name == row[2]:
                        # override this row
                        updated_rows.append([timestamp, lens_name, color_name, r, g, b, brightness, u_prime, v_prime, X, Y, Z])
                        found = True
                    else:
                        updated_rows.append(row)

        # Append new row if not found
        if not found:
            updated_rows.append([timestamp, lens_name, color_name, r, g, b, brightness, u_prime, v_prime, X, Y, Z])

        # Sort: Color using predefined order
        def sort_key(row):
            try:
                lens_index = self.cover_lenses.index(row[1])
            except ValueError:
                lens_index = len(self.cover_lenses)
            try:
                color_index = self.colors.index(row[2])
            except ValueError:
                color_index = len(self.colors)
            return (lens_index, color_index)

        updated_rows.sort(key=sort_key)

        # Write back updated list
        with open(self.calibrated_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "Cover Lens", "Color", "R", "G", "B", "Brightness", "u`", "v`", "X", "Y", "Z"])
            for row in updated_rows:
                writer.writerow(row)

        messagebox.showinfo("Saved", f"Calibration data {'updated' if found else 'added'} to {self.calibrated_path}")

    def refresh_csv_viewer(self):
        if os.path.exists(self.calibrated_path):
            if hasattr(self, 'tree'):
                for i in self.tree.get_children():
                    self.tree.delete(i)

            # Define tag for red text (outside ellipse)
            self.tree.tag_configure("outside_ellipse", foreground="red")

            try:
                with open(self.calibrated_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    headers = next(reader, None)  # skip header

                    for row in reader:
                        try:
                            u = float(row[7])  # u′
                            v = float(row[8])  # v′
                        except (ValueError, IndexError):
                            u = v = 0.0

                        inside = False
                        for e in self.ellipses:
                            cx, cy = e.center
                            major, minor, angle = e.width, e.height, e.angle
                            if self.is_point_in_ellipse(u, v, cx, cy, major, minor, angle):
                                inside = True
                                break

                        if inside:
                            self.tree.insert('', tk.END, values=row)
                        else:
                            self.tree.insert('', tk.END, values=row, tags=("outside_ellipse",))

            except Exception as e:
                messagebox.showerror("Error", f"Failed to read calibrated.csv: {e}")

    def clear_points(self):
        confirm = messagebox.askyesno(
        title="Confirm Clear",
        message="This will delete:\n\n• calibrated.csv\n• calibrated.bin\n• all plotted CIE1931 points\n\nAre you sure you want to continue?"
        )
        if not confirm:
            return
        
        for point in self.plotted_points:
            point.remove()
        for label in self.plotted_labels:
            label.remove()
        self.plotted_points.clear()
        self.plotted_labels.clear()
        self.point_counter = 1
        self.coord_label.config(text="x = ---, y = ---")

        # Remove PASS/FAIL points
        if hasattr(self, "pass_fail_points"):
            for point in self.pass_fail_points:
                point.remove()
            self.pass_fail_points.clear()

        # Clear stored legend labels
        if hasattr(self, "result_labels_shown"):
            self.result_labels_shown.clear()

        # Remove old legends if needed
        if self.ax.get_legend():
            self.ax.get_legend().remove()

        self.canvas.draw()
        """
        if os.path.exists(self.calibrated_path):
           os.remove(self.calibrated_path)
        if hasattr(self, 'tree'):
            for i in self.tree.get_children():
                self.tree.delete(i)

        if os.path.exists(self.calibrated_bin_path):
            os.remove(self.calibrated_bin_path)
        if hasattr(self, 'bin_text'):
            self.bin_text.delete("1.0", tk.END)
        """

    def plot_pass_fail_point(self, x, y, result):
        color = "green" if result == "PASS" else "red"
        label = result if result not in self.result_labels_shown else None
        self.result_labels_shown.add(result)

        scatter = self.ax.scatter([x], [y], color=color, s=20, alpha=0.7, zorder=6, label=label)
        self.pass_fail_points.append(scatter)

        self.coord_label.config(text=f"x = {x:.4f}, y = {y:.4f}")
        self.ax.legend(loc="upper right", fontsize=9)
        self.canvas.draw()

    def clear_pass_fail_points(self):
        # Remove PASS/FAIL points
        if hasattr(self, "pass_fail_points"):
            for point in self.pass_fail_points:
                point.remove()
            self.pass_fail_points.clear()

        # Clear stored legend labels
        if hasattr(self, "result_labels_shown"):
            self.result_labels_shown.clear()

        # Remove old legends if needed
        if self.ax.get_legend():
            self.ax.get_legend().remove()

        self.canvas.draw()

    def draw_bin_viewer_page(self, frame):
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.bin_text = tk.Text(
            text_frame,
            wrap="none",
            font=("Courier", 10),
            yscrollcommand=scrollbar.set
        )
        self.bin_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.bin_text.yview)

        self.load_bin_file()

        logo_frame = tk.Frame(frame, height=46, bg="#e0e0e0")
        logo_frame.pack(fill=tk.X, side=tk.BOTTOM)
        logo_frame.pack_propagate(False)
        self.add_logo_to_frame(logo_frame)

    def load_bin_file(self):
        self.bin_text.delete("1.0", tk.END)
        if not os.path.exists(self.calibrated_bin_path):
            self.create_empty_bin_file()

        led_labels = [f"LED{i+1} {color}" for i in range(8) for color in self.colors]

        with open(self.calibrated_bin_path, "rb") as f:
            data = f.read()
            if len(data) != 151:
                self.bin_text.insert(tk.END, f"Invalid file length: {len(data)} bytes (expected 145)")
                return

            # Header
            signature = data[:4].decode("ascii", errors="ignore")
            length = data[4] + (data[5] << 8)

            self.bin_text.insert(tk.END, f"Signature: {signature}\n")
            self.bin_text.insert(tk.END, f"Length   : {length} bytes\n\n")

            for i in range(48):  # 8x6 = 48 sets
                r, g, b = data[6 + i*3], data[6 + i*3 + 1], data[6 + i*3 + 2]
                label = f"{led_labels[i]:<14}"
                hex_str = f"0x{r:02X} 0x{g:02X} 0x{b:02X}"

                start_index = self.bin_text.index(tk.END)
                self.bin_text.insert(tk.END, f"{label}: {hex_str}  ")
                tag_name = f"color_{i}"
                self.bin_text.insert(tk.END, " ███\n", tag_name)
                self.bin_text.tag_config(tag_name, background=self.rgb_to_hex(r, g, b), foreground=self.rgb_to_hex(r, g, b))

            checksum = data[-1]
            self.bin_text.insert(tk.END, f"\nChecksum: 0x{checksum:02X}")
    
    def save_bin_file(self):
        bin_rgb_data = []

        if not os.path.exists(self.calibrated_path):
            return

        df = pd.read_csv(self.calibrated_path)
        df["Color"] = pd.Categorical(df["Color"], categories=self.colors, ordered=True)
        df.sort_values(by=["LED", "Color"], inplace=True)

        for led in range(1, 9):
            for color in self.colors:
                row = df[(df["LED"] == led) & (df["Color"] == color)]
                if not row.empty:
                    """
                    r = int(row["R"].values[0])
                    g = int(row["G"].values[0])
                    b = int(row["B"].values[0])
                    """
                    try:
                        u = float(row["u`"].values[0])
                        v = float(row["v`"].values[0])
                    except Exception:
                        u = v = 0.0

                    # Check if point is inside any ellipse
                    inside = False
                    for e in self.ellipses:
                        cx, cy = e.center
                        major, minor, angle = e.width, e.height, e.angle
                        if self.is_point_in_ellipse(u, v, cx, cy, major, minor, angle):
                            inside = True
                            break

                    if inside:
                        r = int(row["R"].values[0])
                        g = int(row["G"].values[0])
                        b = int(row["B"].values[0])
                    else:
                        r, g, b = 0, 0, 0  # Outside ellipse → clear RGB
                else:
                    r, g, b = 0, 0, 0  # Default if missing

                bin_rgb_data.extend([r, g, b])

        if len(bin_rgb_data) != 144:
            print("Warning: bin_data is not 144 bytes")

        # Header: Signature ($LED) + Length (0x0090 = 144 bytes)
        signature = list(b"$LED")
        length = [0x90, 0x00]  # Little-endian: 144 bytes
        checksum = (0xFF - sum(bin_rgb_data) % 256) & 0xFF

        final_data = signature + length + bin_rgb_data + [checksum]

        with open(self.calibrated_bin_path, "wb") as f:
            f.write(bytearray(final_data))

        self.load_bin_file()

    def create_empty_bin_file(self):
        signature = list(b"$LED")
        length = [0x90, 0x00]
        null_data = [0x00] * 144
        checksum = (0xFF - sum(null_data) % 256) & 0xFF

        final_data = signature + length + null_data + [checksum]

        with open(self.calibrated_bin_path, "wb") as f:
            f.write(bytearray(final_data))

    def rgb_to_hex(self, r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"

    def create_cie_canvas(self, frame):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    
    app = CalibrationApp(root)
    root.mainloop()
