const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'Server is running!' });
});

// Snow prediction endpoint
app.post('/api/predict', (req, res) => {
    const {
        temperature,
        snowfall_rate,
        snow_depth,
        elevation,
        latitude,
        longitude,
        wind_speed,
        humidity,
        pressure
    } = req.body;

    // Validate inputs
    if (temperature === undefined || latitude === undefined) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    // Path to your Python script
    const pythonScript = path.join(__dirname, 'predict_api.py');

    // Spawn Python process
    const python = spawn('python', [
        pythonScript,
        temperature,
        snowfall_rate,
        snow_depth,
        elevation,
        latitude,
        longitude,
        wind_speed,
        humidity,
        pressure
    ]);

    let dataString = '';
    let errorString = '';

    // Collect data from Python script
    python.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    python.stderr.on('data', (data) => {
        errorString += data.toString();
    });

    // Handle Python script completion
    python.on('close', (code) => {
        if (code !== 0) {
            console.error('Python Error:', errorString);
            return res.status(500).json({ 
                error: 'Prediction failed', 
                details: errorString 
            });
        }

        try {
            const result = JSON.parse(dataString);
            res.json(result);
        } catch (err) {
            console.error('Parse Error:', err);
            res.status(500).json({ 
                error: 'Failed to parse prediction result',
                raw: dataString 
            });
        }
    });
});

app.listen(PORT, () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
});