# PredictMaint - Industrial Predictive Maintenance System

## Overview
PredictMaint is a Desktop UI application built with Python and CustomTkinter designed to monitor the health of 8 virtual machines in a factory setting. It simulates sensor data streams and uses Machine Learning to predict impending failures. It integrates the Gemini 2.5 API to provide natural-language explanations of the ML model's decisions, helping maintenance engineers take immediate, informed action.

## Features
- **Dashboard**: High-level overview of fleet health and active warnings.
- **Fleet View**: Detailed grid showing the status and Remaining Useful Life (RUL) of all 8 machines.
- **Machine Detail**: Real-time sensor trend graphs (Temperature, Vibration, Pressure, Current, RPM) and intermediate ML data transformations.
- **AI Explainer**: Uses Gemini 2.5 Pro to explain the prediction based on feature importance and sensor readings.
- **Model Evaluation**: Compares the ML model's performance against a baseline rule-based system.
- **Settings**: Configuration for the Gemini API Key.

## Installation

1. Clone or download the repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your Gemini API Key in the `.env` file (or enter it in the Settings UI).

## Running the Application
```bash
python main.py
```

Upon first run, the system will automatically:
1. Generate synthetic sensor data for 8 machines (`data/machine_sensor_log.csv`).
2. Train the Random Forest Classifier and Gradient Boosting Regressor models.
3. Save the models to the `models/` directory.

## Project Structure
- `main.py`: Application entry point.
- `ui_app.py`: Main application layout, sidebar navigation, and simulation controls.
- `ui_pages.py`: Implementations of the 6 core UI pages.
- `ui_components.py`: Reusable UI widgets (Graphs, Gauges, Cards).
- `theme.py`: UI color palette (Light Mode) and typography constants.
- `model.py`: ML and baseline rule-based prediction logic, data preprocessing.
- `explainer.py`: Feature importance extraction and baseline local explanations.
- `evaluator.py`: Metrics calculation and model comparison logic.
- `gemini_service.py`: Wrapper for the Gemini 2.5 API.
- `simulation.py`: Real-time data streaming and timing engine.
- `data_generator.py`: Synthetic dataset generator.
