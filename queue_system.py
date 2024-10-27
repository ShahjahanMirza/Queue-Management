import time
from dataclasses import dataclass
from typing import List, Optional
from collections import deque

@dataclass
class Customer:
    id: str
    arrival_time: float
    queue_start_time: float
    service_start_time: Optional[float] = None
    leaving_time: Optional[float] = None
    server_assigned: Optional[int] = None  # Made optional with default None

class ServerMetrics:
    def __init__(self, server_id):
        self.server_id = server_id
        self.total_customers = 0
        self.total_service_time = 0
        self.total_wait_time = 0
        self.total_system_time = 0
        self.idle_time = 0
        self.last_service_end_time = 0

class QueueManagementSystem:
    def __init__(self):
        self.num_servers = 0
        self.servers = []
        self.queues = []  # List of queues, one for each server
        self.setup_complete = False
        self.is_running = False
        self.completed_customers = []
        self.completed_customers_per_server = []  # List of lists for each server
        self.current_time = 0
        self.start_time = None

    def initialize_servers(self, num_servers):
        self.num_servers = num_servers
        self.servers = [None] * num_servers
        self.queues = [deque() for _ in range(num_servers)]
        self.completed_customers_per_server = [[] for _ in range(num_servers)]
        self.setup_complete = True
        self.is_running = True
        self.start_time = time.time()

    def update_current_time(self):
        if self.start_time is not None:
            self.current_time = int(time.time() - self.start_time)

    def get_shortest_queue_index(self):
        queue_lengths = [len(queue) for queue in self.queues]
        return queue_lengths.index(min(queue_lengths))

    def create_customer(self):
        self.update_current_time()
        customer_id = f"C{len(self.completed_customers) + sum(len(q) for q in self.queues) + sum(1 for s in self.servers if s is not None) + 1}"
        return Customer(
            id=customer_id,
            arrival_time=self.current_time,
            queue_start_time=self.current_time
        )

    def handle_enter(self, queue_index):
        if not self.is_running:
            return
        self.update_current_time()
        new_customer = self.create_customer()
        new_customer.server_assigned = queue_index  # Assign the server index
        
        # Check if the selected server is free
        if self.servers[queue_index] is None:
            new_customer.service_start_time = self.current_time
            new_customer.queue_start_time = None
            self.servers[queue_index] = new_customer
        else:
            # Add to the specific queue
            self.queues[queue_index].append(new_customer)
            
    def handle_left(self, server_index):
        if not self.is_running:
            return
        self.update_current_time()
        leaving_customer = self.servers[server_index]
        
        if leaving_customer:
            leaving_customer.leaving_time = self.current_time
            self.completed_customers.append(leaving_customer)
            self.completed_customers_per_server[server_index].append(leaving_customer)

        if self.queues[server_index]:  # Check the specific server's queue
            next_customer = self.queues[server_index].popleft()
            next_customer.service_start_time = self.current_time
            self.servers[server_index] = next_customer
        else:
            self.servers[server_index] = None

    def update_server_metrics(self, server_index, customer):
        metrics = self.server_metrics[server_index]
        metrics.total_customers += 1
        metrics.total_service_time += self.calculate_service_time(customer)
        metrics.total_wait_time += self.calculate_waiting_time(customer)
        metrics.total_system_time += self.calculate_total_time(customer)
        metrics.last_service_end_time = self.current_time

    def handle_stop(self):
        self.is_running = False
        self.update_current_time()

    def calculate_time_difference(self, start, end):
        return end - start if start is not None and end is not None else 0

    def calculate_waiting_time(self, customer):
        if customer.service_start_time and customer.queue_start_time:
            return self.calculate_time_difference(customer.queue_start_time, customer.service_start_time)
        return 0

    def calculate_service_time(self, customer):
        if customer.service_start_time and customer.leaving_time:
            return self.calculate_time_difference(customer.service_start_time, customer.leaving_time)
        return self.calculate_time_difference(customer.arrival_time, customer.leaving_time)

    def calculate_total_time(self, customer):
        return self.calculate_time_difference(customer.arrival_time, customer.leaving_time)

    def calculate_server_specific_metrics(self, server_index):
        metrics = self.server_metrics[server_index]
        total_time_minutes = self.current_time / 60
        
        if total_time_minutes == 0:
            return {
                "Server": f"Server {server_index + 1}",
                "Total Customers": 0,
                "λ (arrival rate)": 0,
                "μ (service rate)": 0,
                "ρ (utilization)": 0,
                "Avg Wait Time": 0,
                "Avg Service Time": 0,
                "Avg System Time": 0,
                "Idle Time (%)": 100,
                "Efficiency (%)": 0
            }

        λ = metrics.total_customers / total_time_minutes
        μ = metrics.total_customers / (metrics.total_service_time / 60) if metrics.total_service_time > 0 else 0
        ρ = λ / μ if μ > 0 else 0
        
        avg_wait = metrics.total_wait_time / metrics.total_customers if metrics.total_customers > 0 else 0
        avg_service = metrics.total_service_time / metrics.total_customers if metrics.total_customers > 0 else 0
        avg_system = metrics.total_system_time / metrics.total_customers if metrics.total_customers > 0 else 0
        
        idle_percentage = (metrics.idle_time / self.current_time) * 100 if self.current_time > 0 else 0
        efficiency = (1 - idle_percentage/100) * 100

        return {
            "Server": f"Server {server_index + 1}",
            "Total Customers": metrics.total_customers,
            "λ (arrival rate)": round(λ, 2),
            "μ (service rate)": round(μ, 2),
            "ρ (utilization)": round(ρ, 2),
            "Avg Wait Time": round(avg_wait/60, 2),
            "Avg Service Time": round(avg_service/60, 2),
            "Avg System Time": round(avg_system/60, 2),
            "Idle Time (%)": round(idle_percentage, 2),
            "Efficiency (%)": round(efficiency, 2)
        }

    def calculate_combined_metrics(self):
        total_customers = sum(metrics.total_customers for metrics in self.server_metrics)
        total_service_time = sum(metrics.total_service_time for metrics in self.server_metrics)
        total_wait_time = sum(metrics.total_wait_time for metrics in self.server_metrics)
        total_system_time = sum(metrics.total_system_time for metrics in self.server_metrics)
        total_idle_time = sum(metrics.idle_time for metrics in self.server_metrics)

        total_time_minutes = self.current_time / 60
        
        if total_time_minutes == 0:
            return {
                "Server": "Overall System",
                "Total Customers": 0,
                "λ (arrival rate)": 0,
                "μ (service rate)": 0,
                "ρ (utilization)": 0,
                "Avg Wait Time": 0,
                "Avg Service Time": 0,
                "Avg System Time": 0,
                "Idle Time (%)": 100,
                "Efficiency (%)": 0
            }

        λ = total_customers / total_time_minutes
        μ = total_customers / (total_service_time / 60) if total_service_time > 0 else 0
        ρ = λ / (self.num_servers * μ) if μ > 0 else 0

        avg_wait = total_wait_time / total_customers if total_customers > 0 else 0
        avg_service = total_service_time / total_customers if total_customers > 0 else 0
        avg_system = total_system_time / total_customers if total_customers > 0 else 0

        idle_percentage = (total_idle_time / (self.current_time * self.num_servers)) * 100 if self.current_time > 0 else 0
        efficiency = (1 - idle_percentage/100) * 100

        return {
            "Server": "Overall System",
            "Total Customers": total_customers,
            "λ (arrival rate)": round(λ, 2),
            "μ (service rate)": round(μ, 2),
            "ρ (utilization)": round(ρ, 2),
            "Avg Wait Time": round(avg_wait/60, 2),
            "Avg Service Time": round(avg_service/60, 2),
            "Avg System Time": round(avg_system/60, 2),
            "Idle Time (%)": round(idle_percentage, 2),
            "Efficiency (%)": round(efficiency, 2)
        }

    def calculate_queue_metrics(self):
        metrics = []
        # Add individual server metrics
        for i in range(self.num_servers):
            metrics.append(self.calculate_server_specific_metrics(i))
        # Add combined metrics
        metrics.append(self.calculate_combined_metrics())
        return metrics

    def calculate_server_metrics(self, server_index):
        """Calculate metrics for a specific server"""
        total_time_minutes = self.current_time / 60
        server_customers = self.completed_customers_per_server[server_index]
        total_customers = len(server_customers)

        # Calculate arrival rate for this server
        λ = total_customers / total_time_minutes if total_time_minutes > 0 else 0

        # Calculate service metrics
        total_service_time = sum(self.calculate_service_time(c) for c in server_customers)
        total_wait_time = sum(self.calculate_waiting_time(c) for c in server_customers)
        total_system_time = sum(self.calculate_total_time(c) for c in server_customers)

        # Calculate server-specific metrics
        μ = total_customers / (total_service_time / 60) if total_service_time > 0 else 0
        ρ = λ / μ if μ > 0 else 0
        Lq = len(self.queues[server_index])  # Current queue length
        Wq = total_wait_time / total_customers / 60 if total_customers > 0 else 0
        L = total_system_time / self.current_time if self.current_time > 0 else 0
        W = total_system_time / total_customers / 60 if total_customers > 0 else 0

        return {
            "Server Number": server_index + 1,
            "Total Customers Served": total_customers,
            "λ (arrival rate)": round(λ, 2),
            "μ (service rate)": round(μ, 2),
            "ρ (utilization)": round(ρ, 2),
            "Lq (current queue length)": round(Lq, 2),
            "Wq (avg wait time in queue)": round(Wq, 2),
            "L (avg number in system)": round(L, 2),
            "W (avg time in system)": round(W, 2),
            "Idle time (%)": round((1 - ρ) * 100, 2) if ρ <= 1 else 0,
            "Efficiency (%)": round(ρ * 100, 2) if ρ <= 1 else 100
        }

    def calculate_overall_metrics(self):
        """Calculate combined metrics for all servers"""
        total_time_minutes = self.current_time / 60
        total_customers = len(self.completed_customers)
        
        # Overall arrival rate
        λ_total = total_customers / total_time_minutes if total_time_minutes > 0 else 0

        # Combined service metrics
        total_service_time = sum(self.calculate_service_time(c) for c in self.completed_customers)
        total_wait_time = sum(self.calculate_waiting_time(c) for c in self.completed_customers)
        total_system_time = sum(self.calculate_total_time(c) for c in self.completed_customers)

        # Calculate overall system metrics
        μ_total = total_customers / (total_service_time / 60) if total_service_time > 0 else 0
        ρ_total = λ_total / (self.num_servers * μ_total) if μ_total > 0 else 0
        Lq_total = sum(len(q) for q in self.queues)  # Total current queue length
        Wq_total = total_wait_time / total_customers / 60 if total_customers > 0 else 0
        L_total = total_system_time / self.current_time if self.current_time > 0 else 0
        W_total = total_system_time / total_customers / 60 if total_customers > 0 else 0

        return {
            "Total Servers": self.num_servers,
            "Total Customers Served": total_customers,
            "System λ (total arrival rate)": round(λ_total, 2),
            "System μ (avg service rate)": round(μ_total, 2),
            "System ρ (overall utilization)": round(ρ_total, 2),
            "System Lq (total queue length)": round(Lq_total, 2),
            "System Wq (avg wait time)": round(Wq_total, 2),
            "System L (avg number in system)": round(L_total, 2),
            "System W (avg time in system)": round(W_total, 2),
            "System Idle time (%)": round((1 - ρ_total) * 100, 2) if ρ_total <= 1 else 0,
            "System Efficiency (%)": round(ρ_total * 100, 2) if ρ_total <= 1 else 100
        }

    def calculate_queue_metrics(self):
        """Calculate metrics for all queues (maintained for compatibility)"""
        return self.calculate_overall_metrics()
