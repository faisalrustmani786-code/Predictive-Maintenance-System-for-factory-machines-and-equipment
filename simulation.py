import pandas as pd
import time

class SimulationEngine:
    def __init__(self):
        self.df = None
        self.is_playing = False
        self.current_step_index = 0
        self.speed_multiplier = 1.0  # 1.0 = normal, 2.0 = fast, 0.5 = slow
        self.base_tick_ms = 1000      # 1 tick = 1 second normally
        self.callbacks = []           # List of functions to call on each tick
        self.root_window = None       # Tkinter root for .after() scheduling
        self._after_id = None
        
        self.unique_timestamps = []
        
    def load_data(self, df):
        """Loads the pre-processed DataFrame into the simulation."""
        self.df = df
        if not self.df.empty:
            self.unique_timestamps = sorted(self.df['timestamp'].unique())
            self.current_step_index = 0
            
    def set_root(self, root):
        """Sets the Tkinter root window needed for scheduling."""
        self.root_window = root
            
    def register_callback(self, callback_func):
        """Register a function to be called on each simulation tick."""
        if callback_func not in self.callbacks:
            self.callbacks.append(callback_func)
            
    def set_speed(self, multiplier):
        """Adjusts playback speed. Valid range is roughly 0.1x to 10x."""
        self.speed_multiplier = max(0.1, min(10.0, multiplier))
        
    def play(self):
        """Starts or resumes the simulation playback."""
        if not self.is_playing and self.root_window and self.df is not None:
            self.is_playing = True
            self._tick()
            
    def pause(self):
        """Pauses the simulation."""
        self.is_playing = False
        if self.root_window and self._after_id:
            self.root_window.after_cancel(self._after_id)
            self._after_id = None
            
    def reset(self):
        """Resets the simulation to the beginning."""
        self.pause()
        self.current_step_index = 0
        self._notify_callbacks() # Update UI with step 0
        
    def get_current_data(self):
        """Returns the data slice for the current timestamp."""
        if self.df is None or self.df.empty or self.current_step_index >= len(self.unique_timestamps):
            return None
            
        current_ts = self.unique_timestamps[self.current_step_index]
        return self.df[self.df['timestamp'] == current_ts]
        
    def _tick(self):
        """Internal method called repeatedly while playing."""
        if not self.is_playing:
            return
            
        if self.current_step_index < len(self.unique_timestamps) - 1:
            self._notify_callbacks()
            self.current_step_index += 1
            
            # Auto-stop logic for demo
            if hasattr(self, 'target_ticks') and self.target_ticks is not None:
                if self.current_step_index >= self.target_ticks:
                    self.pause()
                    if hasattr(self, 'on_complete_callback') and self.on_complete_callback:
                        self.on_complete_callback()
                    return
            
            # Schedule next tick
            delay_ms = int(self.base_tick_ms / self.speed_multiplier)
            self._after_id = self.root_window.after(delay_ms, self._tick)
        else:
            # End of data reached
            self.pause()
            
    def _notify_callbacks(self):
        """Calls all registered callbacks with current data."""
        current_data = self.get_current_data()
        if current_data is not None:
            current_ts = self.unique_timestamps[self.current_step_index]
            for cb in self.callbacks:
                cb(current_ts, current_data)

# Singleton instance
sim_engine = SimulationEngine()
