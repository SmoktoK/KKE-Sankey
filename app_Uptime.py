import uptime_report.demo as demo

if __name__ == "__main__":
    demo.app.run_server(host="127.0.0.1", port=8051, debug=True)