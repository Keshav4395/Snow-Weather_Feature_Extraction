import math
import pandas as pd
import joblib
import sys
import json

# Weight configuration
WEIGHTS = {
    "intercept": -0.20,
    "elev": 1.20,
    "temp": -2.50,
    "sf_rate": 3.00,
    "sd": 1.50,
    "wind": 0.40,
    "hum": 0.60,
    "press": -0.30,
    "lat": 0.50
}

def check_no_snow_thresholds(temp, snowfall_rate, snow_depth, elevation, latitude):
    if temp > 10:
        return True, f"Temperature too high ({temp}°C > 10°C)"
    if abs(latitude) < 30 and elevation < 500:
        return True, f"Tropical region (lat={latitude}°, elev={elevation}m)"
    if snowfall_rate == 0 and snow_depth == 0 and temp > 2:
        return True, f"No snow present and temp above freezing"
    if abs(latitude) < 35 and elevation < 200 and temp > 5:
        return True, f"Low elevation warm region"
    return False, ""

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def normalize_features(temp, snowfall_rate, snow_depth, elevation, latitude, wind, humidity, pressure):
    elev_norm = clamp(elevation / 3000.0)
    lat_norm = clamp(abs(latitude) / 90.0)
    temp_norm = clamp((10.0 - temp) / 40.0)
    sf_rate_norm = clamp(snowfall_rate / 10.0)
    sd_norm = clamp(snow_depth / 200.0)
    wind_norm = clamp(wind / 30.0)
    hum_norm = clamp(humidity / 100.0)
    press_norm = clamp((1050.0 - pressure) / 100.0)
    
    return {
        "elev": elev_norm,
        "lat": lat_norm,
        "temp": temp_norm,
        "sf_rate": sf_rate_norm,
        "sd": sd_norm,
        "wind": wind_norm,
        "hum": hum_norm,
        "press": press_norm
    }

def compute_snow_score(features, W=WEIGHTS):
    z = (
        W["intercept"]
        + W["elev"] * features["elev"]
        + W["temp"] * features["temp"]
        + W["sf_rate"] * features["sf_rate"]
        + W["sd"] * features["sd"]
        + W["wind"] * features["wind"]
        + W["hum"] * features["hum"]
        + W["press"] * features["press"]
        + W["lat"] * features["lat"]
    )
    score = 1.0 / (1.0 + math.exp(-z))
    return score

def main():
    # Get command line arguments
    temp = float(sys.argv[1])
    snowfall_rate = float(sys.argv[2])
    snow_depth = float(sys.argv[3])
    elevation = float(sys.argv[4])
    latitude = float(sys.argv[5])
    longitude = float(sys.argv[6])
    wind = float(sys.argv[7])
    humidity = float(sys.argv[8])
    pressure = float(sys.argv[9])
    
    # Check thresholds
    no_snow, reason = check_no_snow_thresholds(temp, snowfall_rate, snow_depth, elevation, latitude)
    
    if no_snow:
        result = {
            "snow_possible": "NO",
            "reason": reason,
            "snow_score": 0.0,
            "confidence": 100.0
        }
        print(json.dumps(result))
        return
    
    # Load model
    model = joblib.load("snow_model.pkl")
    scaler = joblib.load("scaler.pkl")
    feature_cols = joblib.load("feature_cols.pkl")
    
    # Calculate snow_score
    features = normalize_features(temp, snowfall_rate, snow_depth, elevation, latitude, wind, humidity, pressure)
    snow_score = compute_snow_score(features)
    
    # Prepare input
    input_data = {
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation,
        "snow_score": snow_score
    }
    
    X_input = pd.DataFrame([input_data])[feature_cols]
    X_scaled = scaler.transform(X_input)
    
    # Predict
    prediction = model.predict(X_scaled)[0]
    probability = model.predict_proba(X_scaled)[0]
    
    result = {
        "snow_possible": "YES" if prediction == 1 else "NO",
        "snow_score": round(snow_score, 4),
        "confidence": round(max(probability) * 100, 1),
        "reason": "Model prediction"
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()