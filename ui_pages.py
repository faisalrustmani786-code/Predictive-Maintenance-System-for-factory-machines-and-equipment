import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import theme
from ui_components import GaugeWidget, StatCard, SensorChart, MachineCard, VisualStepIndicator, AIReportCard
from model import get_intermediate_steps, SENSOR_COLS, predict, load_models, preprocess_data
from explainer import get_feature_importance
from evaluator import compare_approaches, evaluate_classifier, evaluate_regressor
from simulation import sim_engine

class UnifiedDashboard(ctk.CTkFrame):
    def __init__(self, master, app_ref, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app_ref
        self.selected_machine_id = None
        
        # Grid layout for the 3 panes
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2) # Left Pane (Fleet)
        self.grid_columnconfigure(1, weight=5) # Center Pane (Details)
        self.grid_columnconfigure(2, weight=3) # Right Pane (AI & Analysis)
        
        self.setup_left_pane()
        self.setup_center_pane()
        self.setup_right_pane()
        
    def setup_left_pane(self):
        self.left_pane = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=0, border_width=1, border_color=theme.BORDER_COLOR)
        self.left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        lbl = ctk.CTkLabel(self.left_pane, text="Fleet Overview", font=theme.FONT_HEADING, text_color=theme.TEXT_PRIMARY)
        lbl.pack(pady=(15, 10), padx=10, anchor="w")
        
        self.fleet_scroll = ctk.CTkScrollableFrame(self.left_pane, fg_color="transparent")
        self.fleet_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.machine_buttons = {}
        
    def setup_center_pane(self):
        self.center_pane = ctk.CTkFrame(self, fg_color="transparent")
        self.center_pane.grid(row=0, column=1, sticky="nsew", padx=5)
        
        self.header_lbl = ctk.CTkLabel(self.center_pane, text="Select a machine from the left", font=theme.FONT_TITLE, text_color=theme.TEXT_PRIMARY)
        self.header_lbl.pack(anchor="w", pady=(0, 15))
        
        # Gauge Frame
        gauge_frame = ctk.CTkFrame(self.center_pane, fg_color=theme.CARD_BG, corner_radius=8, border_width=1, border_color=theme.BORDER_COLOR)
        gauge_frame.pack(fill="x", pady=(0, 10))
        self.gauge = GaugeWidget(gauge_frame, title="Failure Risk", size=150)
        self.gauge.pack(pady=10)
        
        # Charts
        charts_frame = ctk.CTkScrollableFrame(self.center_pane, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True)
        
        self.charts = {}
        row, col = 0, 0
        chart_configs = [
            ("temperature_c", "Temperature (°C)"),
            ("vibration_mm_s", "Vibration (mm/s)"),
            ("pressure_bar", "Pressure (bar)"),
            ("current_a", "Current (A)"),
            ("rpm", "RPM"),
            ("runtime_hours", "Runtime (hrs)")
        ]
        
        for col_name, title in chart_configs:
            chart = SensorChart(charts_frame, title, title.split(" ")[0], height=120)
            chart.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.charts[col_name] = chart
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        
    def setup_right_pane(self):
        self.right_pane = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=0, border_width=1, border_color=theme.BORDER_COLOR)
        self.right_pane.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # 1. Controls
        controls = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        controls.pack(fill="x", padx=10, pady=(15, 10))
        
        lbl = ctk.CTkLabel(controls, text="Simulation & AI Analysis", font=theme.FONT_HEADING, text_color=theme.TEXT_PRIMARY)
        lbl.pack(anchor="w", pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(controls, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        self.btn_demo = ctk.CTkButton(btn_frame, text="▶ Run Demo (1 Min)", command=self.app.start_demo_run, fg_color=theme.PRIMARY_ACCENT)
        self.btn_demo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_stop = ctk.CTkButton(btn_frame, text="⏹ Stop", command=self.app.stop_demo, fg_color=theme.COLOR_CRITICAL)
        self.btn_stop.pack(side="right")
        
        self.progress = ctk.CTkProgressBar(controls)
        self.progress.pack(fill="x", pady=(10, 0))
        self.progress.set(0)
        
        # 2. ML Intermediate Steps
        steps_frame = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        steps_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(steps_frame, text="Live ML Pipeline", font=theme.FONT_MAIN, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.step_indicator = VisualStepIndicator(steps_frame, height=200)
        self.step_indicator.pack(fill="both", expand=True, pady=(5, 0))
        
        # 3. AI Explanation & Evaluation Box
        ai_frame = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        ai_frame.pack(fill="both", expand=True, padx=10, pady=(5, 15))
        
        self.ai_report = AIReportCard(ai_frame)
        self.ai_report.pack(fill="both", expand=True)

    def initialize_fleet(self, machine_ids, machine_types):
        for widget in self.fleet_scroll.winfo_children():
            widget.destroy()
        self.machine_buttons.clear()
        
        for i, m_id in enumerate(machine_ids):
            # Create a simple button for the fleet list
            m_type = machine_types[i]
            btn = ctk.CTkButton(self.fleet_scroll, text=f"{m_id}\n{m_type}", height=60,
                                fg_color="transparent", text_color=theme.TEXT_PRIMARY,
                                border_width=1, border_color=theme.BORDER_COLOR,
                                hover_color=theme.HOVER_COLOR,
                                command=lambda m=m_id: self.select_machine(m))
            btn.pack(fill="x", pady=5)
            self.machine_buttons[m_id] = btn
            
        if machine_ids:
            self.select_machine(machine_ids[0])
            
    def select_machine(self, m_id):
        self.selected_machine_id = m_id
        for mid, btn in self.machine_buttons.items():
            if mid == m_id:
                btn.configure(fg_color=theme.HOVER_COLOR, border_color=theme.PRIMARY_ACCENT, border_width=2)
            else:
                btn.configure(fg_color="transparent", border_color=theme.BORDER_COLOR, border_width=1)
                
        # Force immediate update for this machine
        df_slice = sim_engine.get_current_data()
        self.update_data(df_slice)
        
    def update_data(self, df_slice):
        if df_slice is None or df_slice.empty: return
        
        # 1. Update Fleet Status Colors
        for _, row in df_slice.iterrows():
            m_id = row['machine_id']
            if m_id in self.machine_buttons:
                status = row['health_label']
                color = theme.TEXT_PRIMARY
                if status == "Warning": color = theme.COLOR_WARNING
                elif status == "Critical": color = theme.COLOR_CRITICAL
                # Note: custom button doesn't easily support mixed colors, so we just set text color
                self.machine_buttons[m_id].configure(text_color=color)
        
        # 2. Update Center/Right for Selected Machine
        if not self.selected_machine_id: return
        
        row_df = df_slice[df_slice['machine_id'] == self.selected_machine_id]
        if row_df.empty: return
        row = row_df.iloc[0].to_dict()
        
        self.header_lbl.configure(text=f"{self.selected_machine_id} - {row['machine_type']} | RUL: {row['rul_hours']:.1f} hrs")
        
        clf, reg, scaler, f_cols = load_models()
        if clf:
            proc_df, _ = preprocess_data(row_df)
            label, fail_prob, rul, probs = predict(proc_df, clf, reg, scaler, f_cols)
            
            self.gauge.set_value(fail_prob, label)
            
            steps = get_intermediate_steps(row, proc_df, clf, scaler, f_cols)
            self.step_indicator.update_steps(steps)
            
        for col_name, chart in self.charts.items():
            if col_name in row:
                chart.update_data(row['timestamp'], row[col_name])

    def show_analysis(self, evaluation_text, ai_explanation):
        self.ai_report.update_report(evaluation_text, ai_explanation)
