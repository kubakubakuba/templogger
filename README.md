# Templogger

A simple Python Flask app for monitoring temperature using Arduino / ESP32 boards.

This README is WIP

# WebServer

You can use the provided systemd service to run the Flask app using `gunicorn`. You will need `gnuplot` in order to generate the graphs.

All the temperature measurements are stored in `.tlog` files, which the server app looks for. These files are a simple timestamped temperature measuremets in format:
```
2025-04-02 20:48:52, 25.75
2025-04-02 20:53:52, 25.86
```

# Arduino / ESP32

Dallas temperature sensor ...