// static/js/main.js
new Vue({
    el: '#app',
    data: {
        numServers: 3,
        setupComplete: false,
        isRunning: false,
        currentTime: 0,
        servers: [],
        queue: [],
        customerSummary: [],
        queueMetrics: null
    },
    computed: {
        formattedTime() {
            return this.formatTime(this.currentTime);
        }
    },
    methods: {
        initializeSimulation() {
            axios.post('/api/initialize', { numServers: this.numServers })
                .then(() => {
                    this.setupComplete = true;
                    this.isRunning = true;
                    this.startTimer();
                    this.fetchStatus();
                });
        },
        customerEnter() {
            axios.post('/api/enter')
                .then(() => this.fetchStatus());
        },
        customerLeave(serverIndex) {
            axios.post('/api/leave', { serverIndex })
                .then(() => this.fetchStatus());
        },
        stopSimulation() {
            axios.post('/api/stop')
                .then(() => {
                    this.isRunning = false;
                    clearInterval(this.timer);
                    this.fetchSummary();
                });
        },
        fetchStatus() {
            axios.get('/api/status')
                .then(response => {
                    const oldServers = this.servers;
                    this.servers = response.data.servers.map((server, index) => {
                        if (server && (!oldServers[index] || server.id !== oldServers[index].id)) {
                            return { ...server, isNew: true };
                        }
                        return server;
                    });
                    this.queue = response.data.queue;
                    this.currentTime = response.data.currentTime;
                    this.isRunning = response.data.isRunning;
                    
                    // Remove the 'isNew' flag after animation
                    setTimeout(() => {
                        this.servers = this.servers.map(server => {
                            if (server) {
                                return { ...server, isNew: false };
                            }
                            return server;
                        });
                    }, 500);
                });
        },
        fetchSummary() {
            axios.get('/api/summary')
                .then(response => {
                    this.customerSummary = response.data.customerSummary;
                    this.queueMetrics = response.data.queueMetrics;
                });
        },
        startTimer() {
            this.timer = setInterval(() => {
                this.currentTime++;
                this.fetchStatus();
            }, 1000);
        },
        formatTime(seconds) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        },
        downloadCustomerEntries() {
            window.location.href = '/api/download/customers';
        },
        downloadStatistics() {
            window.location.href = '/api/download/metrics';
        },
        resetSimulation() {
            axios.post('/api/reset')
                .then(() => {
                    this.setupComplete = false;
                    this.isRunning = false;
                    this.currentTime = 0;
                    this.servers = [];
                    this.queue = [];
                    this.customerSummary = [];
                    this.queueMetrics = null;
                    clearInterval(this.timer);
                });
        }
    },
    created() {
        // Check if the simulation is already running when the page loads
        axios.get('/api/status')
            .then(response => {
                if (response.data.isRunning) {
                    this.setupComplete = true;
                    this.isRunning = true;
                    this.startTimer();
                    this.fetchStatus();
                }
            });
    }
});