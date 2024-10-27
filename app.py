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
  queue_index = int(request.json.get('queueIndex', 0))
  qms.handle_enter(queue_index)
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
      'queues': [[c.id for c in queue] for queue in qms.queues],
      'currentTime': qms.current_time,
      'isRunning': qms.is_running
  })

@app.route('/api/summary', methods=['GET'])
def get_summary():
    qms.update_current_time()
    server_summaries = []

    # Get individual server summaries
    for i in range(qms.num_servers):
        customer_summary = [
            {
                'id': c.id,
                'arrivalTime': c.arrival_time,
                'waitingTime': qms.calculate_waiting_time(c),
                'serviceTime': qms.calculate_service_time(c),
                'totalTime': qms.calculate_total_time(c)
            } for c in qms.completed_customers_per_server[i]
        ]
        server_summaries.append({
            'serverIndex': i,
            'customerSummary': customer_summary,
            'metrics': qms.calculate_server_metrics(i)
        })

    return jsonify({
        'serverSummaries': server_summaries,
        'overallMetrics': qms.calculate_overall_metrics(),
        'currentTime': qms.current_time
    })

@app.route('/api/download/customers/<int:server_index>', methods=['GET'])
def download_customers(server_index):
  csv_data = "Customer ID,Arrival Time (min),Waiting Time (min),Service Time (min),Total Time (min)\n"
  for c in qms.completed_customers_per_server[server_index]:
      arrival_time_min = c.arrival_time / 60
      waiting_time_min = qms.calculate_waiting_time(c) / 60
      service_time_min = qms.calculate_service_time(c) / 60
      total_time_min = qms.calculate_total_time(c) / 60
      csv_data += f"{c.id},{arrival_time_min:.2f},{waiting_time_min:.2f},{service_time_min:.2f},{total_time_min:.2f}\n"
  return app.response_class(
      csv_data,
      mimetype='text/csv',
      headers={"Content-disposition": f"attachment; filename=server_{server_index}_customers.csv"}
  )

@app.route('/api/download/metrics', methods=['GET'])
def download_metrics():
  csv_data = "Server,Metric,Value\n"
  # Individual server metrics
  for i in range(qms.num_servers):
      metrics = qms.calculate_server_metrics(i)
      for key, value in metrics.items():
          csv_data += f"Server {i},{key},{value}\n"
  
  # Overall metrics
  overall_metrics = qms.calculate_overall_metrics()
  for key, value in overall_metrics.items():
      csv_data += f"Overall,{key},{value}\n"
  
  return app.response_class(
      csv_data,
      mimetype='text/csv',
      headers={"Content-disposition": "attachment; filename=queue_statistics.csv"}
  )

@app.route('/api/reset', methods=['POST'])
def reset_api():
  global qms
  qms = QueueManagementSystem()
  return jsonify(success=True)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=10000)
