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

class QueueManagementSystem:
    def __init__(self):
        self.num_servers = 0
        self.servers = []
        self.queue = deque()
        self.setup_complete = False
        self.is_running = False
        self.completed_customers = []
        self.current_time = 0
        self.start_time = None

    def initialize_servers(self, num_servers):
        self.num_servers = num_servers
        self.servers = [None] * num_servers
        self.setup_complete = True
        self.is_running = True
        self.start_time = time.time()

    def update_current_time(self):
        if self.start_time is not None:
            self.current_time = int(time.time() - self.start_time)

    def create_customer(self):
        self.update_current_time()
        return Customer(
            id=f"C{len(self.completed_customers) + len(self.queue) + sum(1 for s in self.servers if s is not None) + 1}",
            arrival_time=self.current_time,
            queue_start_time=self.current_time
        )

    def handle_enter(self):
        if not self.is_running:
            return
        self.update_current_time()
        new_customer = self.create_customer()
        empty_server_index = next((i for i, server in enumerate(self.servers) if server is None), None)
        
        if empty_server_index is not None:
            new_customer.service_start_time = self.current_time
            new_customer.queue_start_time = None
            self.servers[empty_server_index] = new_customer
        else:
            self.queue.append(new_customer)

    def handle_left(self, server_index):
        if not self.is_running:
            return
        self.update_current_time()
        leaving_customer = self.servers[server_index]
        
        if leaving_customer:
            leaving_customer.leaving_time = self.current_time
            self.completed_customers.append(leaving_customer)

        if self.queue:
            next_customer = self.queue.popleft()
            next_customer.service_start_time = self.current_time
            self.servers[server_index] = next_customer
        else:
            self.servers[server_index] = None

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

    def calculate_queue_metrics(self):
        total_time_minutes = self.current_time / 60
        total_customers = len(self.completed_customers)
        λ = total_customers / total_time_minutes if total_time_minutes > 0 else 0

        total_service_time = sum(self.calculate_service_time(c) for c in self.completed_customers)
        total_wait_time = sum(self.calculate_waiting_time(c) for c in self.completed_customers)
        total_system_time = sum(self.calculate_total_time(c) for c in self.completed_customers)

        μ = total_customers / (total_service_time / 60) if total_service_time > 0 else 0
        ρ = λ / (self.num_servers * μ) if μ > 0 else 0
        Lq = total_wait_time / self.current_time if self.current_time > 0 else 0
        Wq = total_wait_time / total_customers / 60 if total_customers > 0 else 0
        L = total_system_time / self.current_time if self.current_time > 0 else 0
        W = total_system_time / total_customers / 60 if total_customers > 0 else 0

        return {
            "λ (arrival rate)": round(λ, 2),
            "μ (service rate)": round(μ, 2),
            "ρ (utilization)": round(ρ, 2),
            "Lq (avg queue length)": round(Lq, 2),
            "Wq (avg wait time in queue)": round(Wq, 2),
            "L (avg number in system)": round(L, 2),
            "W (avg time in system)": round(W, 2),
            "Idle time (%)": round((1 - ρ) * 100, 2),
            "Efficiency (%)": round(ρ * 100, 2)
        }