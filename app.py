from flask import Flask, render_template, request, jsonify, redirect, url_for
from queue_system import QueueManagementSystem
import time

app = Flask(__name__)
qms = QueueManagementSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/initialize', methods=['POST'])
def initialize():
    num_servers = int(request.json['numServers'])
    qms.initialize_servers(num_servers)
    return jsonify(success=True)

@app.route('/api/enter', methods=['POST'])
def customer_enter():
    qms.handle_enter()
    return jsonify(success=True)

@app.route('/api/leave', methods=['POST'])
def customer_leave():
    server_index = int(request.json['serverIndex'])
    qms.handle_left(server_index)
    return jsonify(success=True)

@app.route('/api/stop', methods=['POST'])
def stop_simulation():
    qms.handle_stop()
    return jsonify(success=True)

@app.route('/api/status', methods=['GET'])
def get_status():
    qms.update_current_time()
    return jsonify({
        'servers': [{'id': s.id if s else None} for s in qms.servers],
        'queue': [c.id for c in qms.queue],
        'currentTime': qms.current_time,
        'isRunning': qms.is_running
    })

@app.route('/api/summary', methods=['GET'])
def get_summary():
    qms.update_current_time()
    customer_summary = [
        {
            'id': c.id,
            'arrivalTime': c.arrival_time,
            'waitingTime': qms.calculate_waiting_time(c),
            'serviceTime': qms.calculate_service_time(c),
            'totalTime': qms.calculate_total_time(c)
        } for c in qms.completed_customers
    ]
    return jsonify({
        'customerSummary': customer_summary,
        'queueMetrics': qms.calculate_queue_metrics(),
        'currentTime': qms.current_time
    })

@app.route('/api/download/customers', methods=['GET'])
def download_customers():
    csv_data = "Customer ID,Arrival Time (min),Waiting Time (min),Service Time (min),Total Time (min)\n"
    for c in qms.completed_customers:
        arrival_time_min = c.arrival_time / 60
        waiting_time_min = qms.calculate_waiting_time(c) / 60
        service_time_min = qms.calculate_service_time(c) / 60
        total_time_min = qms.calculate_total_time(c) / 60
        csv_data += f"{c.id},{arrival_time_min:.2f},{waiting_time_min:.2f},{service_time_min:.2f},{total_time_min:.2f}\n"
    return app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=customer_entries.csv"}
    )

@app.route('/api/download/metrics', methods=['GET'])
def download_metrics():
    metrics = qms.calculate_queue_metrics()
    csv_data = "Metric,Value\n"
    for key, value in metrics.items():
        csv_data += f"{key},{value}\n"
    return app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=queue_statistics.csv"}
    )

@app.route('/summary')
def summary():
    # ... existing summary code ...
    return render_template('summary.html', stats=stats)

@app.route('/reset', methods=['POST'])
def reset():
    global simulation, stats
    simulation = None
    stats = None
    return redirect(url_for('index'))

@app.route('/api/reset', methods=['POST'])
def reset_api():
    global qms
    qms = QueueManagementSystem()
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)