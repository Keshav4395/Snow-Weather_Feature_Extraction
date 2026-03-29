import math
import pandas as pd
import joblib
import os

# Weight configuration for snow_score calculation
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

# ============== THRESHOLD RULES ==============
def check_no_snow_thresholds(temp, snowfall_rate, snow_depth, elevation, latitude):
    """
    Hard threshold rules - if ANY condition met, immediately return NO SNOW
    """
    # Rule 1: Too hot - physically impossible for snow
    if temp > 10:
        return True, f"Temperature too high ({temp}°C > 10°C)"
    
    # Rule 2: Tropical/equatorial region with no snow
    if abs(latitude) < 30 and elevation < 500:
        return True, f"Tropical region (lat={latitude}°, elev={elevation}m)"
    
    # Rule 3: No snowfall AND warm
    if snowfall_rate == 0 and snow_depth == 0 and temp > 2:
        return True, f"No snow present and temp above freezing"
    
    # Rule 4: Very low elevation tropical
    if abs(latitude) < 35 and elevation < 200 and temp > 5:
        return True, f"Low elevation warm region"
    
    return False, ""

# ============================================

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
    print("\n=== Snow Possibility Predictor ===\n")
    
    # Load model artifacts
    if not os.path.exists("snow_model.pkl") or not os.path.exists("scaler.pkl"):
        print("ERROR: Model files not found. Run train_model.py first.")
        return
    
    model = joblib.load("snow_model.pkl")
    scaler = joblib.load("scaler.pkl")
    feature_cols = joblib.load("feature_cols.pkl")
    
    print("Enter weather and location data:\n")
    
    # Collect inputs
    temp = float(input("Temperature (°C): "))
    snowfall_rate = float(input("Snowfall rate (cm/hr): "))
    snow_depth = float(input("Snow depth (cm): "))
    elevation = float(input("Elevation (m): "))
    latitude = float(input("Latitude: "))
    longitude = float(input("Longitude: "))
    wind = float(input("Wind speed (m/s): "))
    humidity = float(input("Humidity (%): "))
    pressure = float(input("Pressure (hPa): "))
    
    # ========== CHECK THRESHOLD RULES FIRST ==========
    no_snow, reason = check_no_snow_thresholds(temp, snowfall_rate, snow_depth, elevation, latitude)
    
    if no_snow:
        print("\n" + "="*40)
        print(f"Snow Possible: ✗ NO")
        print(f"Reason: {reason}")
        print("="*40 + "\n")
        return
    # ================================================
    
    # Calculate snow_score
    features = normalize_features(
        temp=temp,
        snowfall_rate=snowfall_rate,
        snow_depth=snow_depth,
        elevation=elevation,
        latitude=latitude,
        wind=wind,
        humidity=humidity,
        pressure=pressure
    )
    snow_score = compute_snow_score(features)
    
    # Prepare input matching training features
    input_data = {
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation,
        "snow_score": snow_score
    }
    
    # Ensure feature order matches training
    X_input = pd.DataFrame([input_data])[feature_cols]
    X_scaled = scaler.transform(X_input)
    
    # Predict
    prediction = model.predict(X_scaled)[0]
    probability = model.predict_proba(X_scaled)[0]
    
    print("\n" + "="*40)
    print(f"Calculated Snow Score: {snow_score:.4f}")
    print(f"Snow Possible: {'✓ YES' if prediction == 1 else '✗ NO'}")
    print(f"Confidence: {max(probability)*100:.1f}%")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
