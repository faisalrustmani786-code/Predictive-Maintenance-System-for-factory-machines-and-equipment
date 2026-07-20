import customtkinter as ctk
import os
import threading
from tkinter import messagebox
import theme
from simulation import sim_engine
from ui_pages import UnifiedDashboard
from model import load_data, preprocess_data, train_models, load_models, rule_based_predict, LABEL_MAPPING
from evaluator import compare_approaches

class PredictMaintApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("PredictMaint - Unified Dashboard")
        self.geometry("1400x900")
        self.configure(fg_color=theme.BG_COLOR)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.full_df = None
        
        self.dashboard = UnifiedDashboard(self, self)
        self.dashboard.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Load models / data in background
        self.show_loading()
        threading.Thread(target=self.initialize_system, daemon=True).start()
        
    def start_demo_run(self):
        """Starts the time-boxed simulation (e.g. 120 ticks = 1-2 mins depending on speed)"""
        # Set speed to 5x so it goes fast
        sim_engine.set_speed(5.0)
        
        # We want to run for about 120 ticks (which is 10 hours of simulated time, 5 mins per tick)
        sim_engine.target_ticks = sim_engine.current_step_index + 120
        sim_engine.on_complete_callback = self.on_demo_complete
        
        self.dashboard.btn_demo.configure(state="disabled", text="Running Demo...")
        self.dashboard.progress.set(0)
        
        sim_engine.play()
        self.update_progress()
        
    def stop_demo(self):
        sim_engine.pause()
        self.dashboard.btn_demo.configure(state="normal", text="▶ Run Demo (1 Min)")
        
    def update_progress(self):
        if sim_engine.is_playing and hasattr(sim_engine, 'target_ticks'):
            # Calculate progress
            start = sim_engine.target_ticks - 120
            current = sim_engine.current_step_index - start
            prog = max(0.0, min(1.0, current / 120.0))
            self.dashboard.progress.set(prog)
            
            # Re-schedule
            self.after(200, self.update_progress)
            
    def on_demo_complete(self):
        self.dashboard.progress.set(1.0)
        self.dashboard.btn_demo.configure(state="normal", text="▶ Run Demo (1 Min)")
        
        # 1. Run Evaluation
        eval_text = self._run_evaluation()
        
        # 2. Get Gemini Explanation for current machine
        m_id = self.dashboard.selected_machine_id
        ai_text = self._run_gemini(m_id)
        
        # 3. Update UI
        self.dashboard.show_analysis(eval_text, ai_text)
        
    def _run_evaluation(self):
        try:
            df = self.full_df
            clf, reg, scaler, f_cols = load_models()
            proc_df, _ = preprocess_data(df)
            
            y_true_class = df['health_label'].map(LABEL_MAPPING).values
            X_scaled = scaler.transform(proc_df[f_cols].values)
            y_pred_ml_class = clf.predict(X_scaled)
            
            y_pred_rule_class = []
            for _, row in df.iterrows():
                lbl, rul = rule_based_predict(row)
                y_pred_rule_class.append(LABEL_MAPPING[lbl])
                
            ml_acc = (y_true_class == y_pred_ml_class).mean()
            rule_acc = (y_true_class == np.array(y_pred_rule_class)).mean()
            
            return f"ML Accuracy: {ml_acc:.1%} | Rule Baseline: {rule_acc:.1%}"
        except Exception as e:
            return f"Eval Error: {e}"
            
    def _run_gemini(self, m_id):
        from gemini_service import gemini_service
        from model import predict, preprocess_data
        from explainer import get_feature_importance
        
        df_slice = sim_engine.get_current_data()
        if df_slice is None or df_slice.empty: return "No data available."
        
        row_df = df_slice[df_slice['machine_id'] == m_id]
        if row_df.empty: return "Machine not found."
        
        clf, reg, scaler, f_cols = load_models()
        row = row_df.iloc[0].to_dict()
        proc_df, _ = preprocess_data(row_df)
        label, fail_prob, rul, _ = predict(proc_df, clf, reg, scaler, f_cols)
        feat_imp = get_feature_importance(clf, f_cols)
        
        return gemini_service.explain_prediction(row, label, fail_prob, rul, feat_imp)

    def on_sim_tick(self, timestamp, df_slice):
        self.dashboard.update_data(df_slice)
                    
    def show_loading(self):
        self.loading_win = ctk.CTkToplevel(self)
        self.loading_win.title("Initializing")
        self.loading_win.geometry("300x150")
        self.loading_win.attributes('-topmost', 'true')
        self.loading_win.protocol("WM_DELETE_WINDOW", lambda: None)
        
        lbl = ctk.CTkLabel(self.loading_win, text="Loading data and models...", font=theme.FONT_HEADING)
        lbl.pack(expand=True)
        
    def initialize_system(self):
        import numpy as np
        # Need to expose numpy globally for eval method
        global np
        try:
            if not os.path.exists("data/machine_sensor_log.csv"):
                from data_generator import generate_synthetic_data
                generate_synthetic_data()
                
            self.full_df = load_data()
            clf, reg, scaler, f_cols = load_models()
            if not clf:
                proc_df, f_cols = preprocess_data(self.full_df)
                train_models(proc_df, f_cols)
                
            sim_engine.set_root(self)
            sim_engine.load_data(self.full_df)
            sim_engine.register_callback(self.on_sim_tick)
            
            machine_ids = sorted(self.full_df['machine_id'].unique())
            types = []
            for mid in machine_ids:
                m_type = self.full_df[self.full_df['machine_id'] == mid]['machine_type'].iloc[0]
                types.append(m_type)
                
            self.after(0, lambda: self._finish_initialization(machine_ids, types))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Initialization Error", str(e)))
            
    def _finish_initialization(self, machine_ids, types):
        self.loading_win.destroy()
        self.dashboard.initialize_fleet(machine_ids, types)
        self.on_sim_tick(None, sim_engine.get_current_data())

if __name__ == "__main__":
    app = PredictMaintApp()
    app.mainloop()
