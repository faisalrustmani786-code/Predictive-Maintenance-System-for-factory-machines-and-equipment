import customtkinter as ctk
import tkinter as tk
import math
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import theme

class GaugeWidget(ctk.CTkFrame):
    def __init__(self, master, title="Health", size=150, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.size = size
        self.value = 100
        self.color = theme.COLOR_NORMAL
        
        self.canvas = tk.Canvas(self, width=size, height=size, bg=theme.BG_COLOR, highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")
        
        self.title_label = ctk.CTkLabel(self, text=title, font=theme.FONT_MAIN, text_color=theme.TEXT_SECONDARY)
        self.title_label.place(relx=0.5, rely=0.85, anchor="center")
        
        self.value_label = ctk.CTkLabel(self, text="100%", font=theme.FONT_TITLE, text_color=theme.TEXT_PRIMARY)
        self.value_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.draw_gauge()
        
    def set_value(self, value, status="Normal"):
        self.value = max(0, min(100, value))
        self.value_label.configure(text=f"{int(self.value)}%")
        
        if status == "Normal":
            self.color = theme.COLOR_NORMAL
        elif status == "Warning":
            self.color = theme.COLOR_WARNING
        else:
            self.color = theme.COLOR_CRITICAL
            
        self.draw_gauge()
        
    def draw_gauge(self):
        self.canvas.delete("all")
        padding = 10
        bbox = (padding, padding, self.size - padding, self.size - padding)
        
        # Draw background track (gray)
        self.canvas.create_arc(bbox, start=180, extent=-180, style=tk.ARC, width=12, outline=theme.BORDER_COLOR)
        
        # Draw value arc
        extent = -(self.value / 100.0) * 180
        self.canvas.create_arc(bbox, start=180, extent=extent, style=tk.ARC, width=12, outline=self.color)

class StatCard(ctk.CTkFrame):
    def __init__(self, master, title, value, unit="", **kwargs):
        super().__init__(master, fg_color=theme.CARD_BG, corner_radius=8, border_width=1, border_color=theme.BORDER_COLOR, **kwargs)
        
        self.title_label = ctk.CTkLabel(self, text=title, font=theme.FONT_MAIN, text_color=theme.TEXT_SECONDARY)
        self.title_label.pack(anchor="w", padx=15, pady=(15, 0))
        
        self.val_var = tk.StringVar(value=f"{value} {unit}")
        self.unit = unit
        
        self.val_label = ctk.CTkLabel(self, textvariable=self.val_var, font=theme.FONT_LARGE_NUMBER, text_color=theme.TEXT_PRIMARY)
        self.val_label.pack(anchor="w", padx=15, pady=(5, 15))
        
    def set_value(self, value):
        self.val_var.set(f"{value} {self.unit}")

class SensorChart(ctk.CTkFrame):
    def __init__(self, master, title, ylabel, height=200, **kwargs):
        super().__init__(master, fg_color=theme.CARD_BG, corner_radius=8, border_width=1, border_color=theme.BORDER_COLOR, **kwargs)
        
        self.title = title
        self.ylabel = ylabel
        
        lbl = ctk.CTkLabel(self, text=title, font=theme.FONT_HEADING, text_color=theme.TEXT_PRIMARY)
        lbl.pack(anchor="w", padx=10, pady=5)
        
        self.fig = Figure(figsize=(5, height/100), dpi=100)
        self.fig.patch.set_facecolor(theme.CARD_BG)
        
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(theme.CARD_BG)
        self.ax.tick_params(colors=theme.TEXT_SECONDARY)
        for spine in self.ax.spines.values():
            spine.set_color(theme.BORDER_COLOR)
            
        self.line, = self.ax.plot([], [], color=theme.PRIMARY_ACCENT, linewidth=2)
        self.ax.set_ylabel(ylabel, color=theme.TEXT_SECONDARY)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        self.x_data = []
        self.y_data = []
        
    def update_data(self, new_x, new_y):
        self.x_data.append(new_x)
        self.y_data.append(new_y)
        
        # Keep last 50 points to prevent memory issues and keep chart readable
        if len(self.x_data) > 50:
            self.x_data.pop(0)
            self.y_data.pop(0)
            
        self.line.set_xdata(range(len(self.x_data)))
        self.line.set_ydata(self.y_data)
        
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()
        
    def clear(self):
        self.x_data = []
        self.y_data = []
        self.line.set_xdata([])
        self.line.set_ydata([])
        self.canvas.draw_idle()

class MachineCard(ctk.CTkFrame):
    def __init__(self, master, machine_id, machine_type, click_callback=None, **kwargs):
        super().__init__(master, fg_color=theme.CARD_BG, corner_radius=8, border_width=2, border_color=theme.BORDER_COLOR, **kwargs)
        self.machine_id = machine_id
        self.click_callback = click_callback
        
        self.bind("<Button-1>", self._on_click)
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        header.bind("<Button-1>", self._on_click)
        
        ctk.CTkLabel(header, text=machine_id, font=theme.FONT_HEADING, text_color=theme.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text=machine_type, font=theme.FONT_MAIN, text_color=theme.TEXT_SECONDARY).pack(side="right")
        
        self.status_label = ctk.CTkLabel(self, text="Normal", font=theme.FONT_MAIN, fg_color=theme.COLOR_NORMAL, text_color="white", corner_radius=4)
        self.status_label.pack(pady=5)
        self.status_label.bind("<Button-1>", self._on_click)
        
        self.rul_label = ctk.CTkLabel(self, text="RUL: -- hrs", font=theme.FONT_NUMBER, text_color=theme.TEXT_PRIMARY)
        self.rul_label.pack(pady=(0, 10))
        self.rul_label.bind("<Button-1>", self._on_click)
        
    def update_status(self, status, rul):
        self.rul_label.configure(text=f"RUL: {rul:.1f} hrs")
        self.status_label.configure(text=status)
        
        if status == "Normal":
            self.status_label.configure(fg_color=theme.COLOR_NORMAL)
            self.configure(border_color=theme.BORDER_COLOR)
        elif status == "Warning":
            self.status_label.configure(fg_color=theme.COLOR_WARNING)
            self.configure(border_color=theme.COLOR_WARNING)
        else:
            self.status_label.configure(fg_color=theme.COLOR_CRITICAL)
            self.configure(border_color=theme.COLOR_CRITICAL)
            
    def _on_click(self, event):
        if self.click_callback:
            self.click_callback(self.machine_id)

class AlertToast:
    """A floating, auto-dismissing toast notification."""
    def __init__(self, parent, message, level="info", duration=3000):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent, fg_color=theme.CARD_BG, border_width=1, corner_radius=8)
        
        color = theme.PRIMARY_ACCENT
        if level == "warning": color = theme.COLOR_WARNING
        elif level == "critical": color = theme.COLOR_CRITICAL
            
        self.frame.configure(border_color=color)
        
        lbl = ctk.CTkLabel(self.frame, text=message, font=theme.FONT_MAIN, text_color=theme.TEXT_PRIMARY, wraplength=250)
        lbl.pack(padx=15, pady=10)
        
        # Place at bottom right
        self.frame.place(relx=0.98, rely=0.9, anchor="se")
        
        parent.after(duration, self.dismiss)
        
    def dismiss(self):
        self.frame.destroy()

class VisualStepIndicator(ctk.CTkScrollableFrame):
    """Shows the 4-step pipeline process visually."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.c1, self.c1_content = self._create_step_card("1. Sensor Telemetry", theme.PRIMARY_ACCENT)
        self._create_connector()
        self.c2, self.c2_content = self._create_step_card("2. Feature Extraction", "#8B5CF6") # Purple
        self._create_connector()
        self.c3, self.c3_content = self._create_step_card("3. Model Inference", "#F59E0B") # Amber
        self._create_connector()
        self.c4, self.c4_content = self._create_step_card("4. Prediction Output", theme.COLOR_CRITICAL)
        
        self.c4_label = ctk.CTkLabel(self.c4_content, text="--", font=theme.FONT_HEADING, corner_radius=6)
        self.c4_label.pack(fill="x", pady=5)
        
    def _create_step_card(self, title, color):
        card = ctk.CTkFrame(self, fg_color=theme.CARD_BG, border_width=1, border_color=theme.BORDER_COLOR, corner_radius=8)
        card.pack(fill="x", padx=5)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        dot = ctk.CTkFrame(header, width=12, height=12, corner_radius=6, fg_color=color)
        dot.pack(side="left", pady=5)
        
        lbl = ctk.CTkLabel(header, text=title, font=theme.FONT_MAIN, text_color=theme.TEXT_PRIMARY)
        lbl.pack(side="left", padx=10)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=10, pady=(0, 10))
        return card, content
        
    def _create_connector(self):
        conn = ctk.CTkFrame(self, width=2, height=12, fg_color=theme.BORDER_COLOR)
        conn.pack(pady=2)

    def update_steps(self, steps_dict):
        # 1. Sensors
        for widget in self.c1_content.winfo_children(): widget.destroy()
        row, col = 0, 0
        for k, v in steps_dict.get("1. Raw Sensors", {}).items():
            lbl = ctk.CTkLabel(self.c1_content, text=f"{k.split('_')[0]}: {v}", font=("JetBrains Mono", 11), text_color=theme.TEXT_SECONDARY)
            lbl.grid(row=row, column=col, padx=5, sticky="w")
            col += 1
            if col > 1: col = 0; row += 1
            
        # 2. Features
        for widget in self.c2_content.winfo_children(): widget.destroy()
        for k, v in steps_dict.get("2. Engineered Features", {}).items():
            lbl = ctk.CTkLabel(self.c2_content, text=f"{k}: {v}", font=("JetBrains Mono", 11), text_color=theme.TEXT_SECONDARY)
            lbl.pack(anchor="w")
            
        # 3. Model
        for widget in self.c3_content.winfo_children(): widget.destroy()
        probs = steps_dict.get("3. Model Probabilities", {})
        colors = {"Normal": theme.COLOR_NORMAL, "Warning": theme.COLOR_WARNING, "Critical": theme.COLOR_CRITICAL}
        for k, v_str in probs.items():
            frame = ctk.CTkFrame(self.c3_content, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text=k, font=("JetBrains Mono", 11), width=60, anchor="w").pack(side="left")
            
            val = float(v_str.strip('%')) / 100.0
            bar = ctk.CTkProgressBar(frame, fg_color=theme.BORDER_COLOR, progress_color=colors[k], height=8)
            bar.pack(side="left", fill="x", expand=True, padx=5)
            bar.set(val)
            
            ctk.CTkLabel(frame, text=v_str, font=("JetBrains Mono", 11), width=40, anchor="e").pack(side="right")
            
        # 4. Output
        out = steps_dict.get("4. Final Output", "--")
        self.c4_label.configure(text=out, fg_color=colors.get(out, theme.CARD_BG), text_color="white" if out in colors else theme.TEXT_PRIMARY)


class AIReportCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Metrics
        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_frame.pack(fill="x", pady=(0, 10))
        
        self.acc_card = StatCard(self.metrics_frame, "ML Acc", "--", "%")
        self.acc_card.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.base_card = StatCard(self.metrics_frame, "Rule Acc", "--", "%")
        self.base_card.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # AI Insight Bubble
        self.bubble = ctk.CTkFrame(self, fg_color=theme.CARD_BG, border_width=2, border_color=theme.PRIMARY_ACCENT, corner_radius=12)
        self.bubble.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(self.bubble, fg_color=theme.PRIMARY_ACCENT, corner_radius=0)
        header.pack(fill="x", padx=2, pady=2)
        
        ctk.CTkLabel(header, text="✨ Gemini AI Insights", font=theme.FONT_HEADING, text_color="white").pack(anchor="w", padx=10, pady=5)
        
        self.textbox = ctk.CTkTextbox(self.bubble, font=theme.FONT_MAIN, text_color=theme.TEXT_PRIMARY, fg_color="transparent", wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("1.0", "Press 'Run Demo' to start. Insights will appear here.")
        self.textbox.configure(state="disabled")
        
    def update_report(self, eval_text, ai_text):
        try:
            parts = eval_text.split('|')
            ml_acc = parts[0].split(':')[1].strip().replace('%', '')
            rule_acc = parts[1].split(':')[1].strip().replace('%', '')
            self.acc_card.set_value(ml_acc)
            self.base_card.set_value(rule_acc)
        except Exception:
            pass
            
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", ai_text)
        self.textbox.configure(state="disabled")
