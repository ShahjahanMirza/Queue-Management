// static/js/main.js
new Vue({
    el: '#app',
    data: {
        numServers: 3,
        setupComplete: false,
        isRunning: false,
        currentTime: 0,
        servers: [],
        queues: [],
        serverSummaries: [],
        overallMetrics: null,
        selectedQueue: 0
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
        customerEnter(queueIndex) {
            axios.post('/api/enter', { queueIndex })
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
                    this.queues = response.data.queues;
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
                    this.serverSummaries = response.data.serverSummaries;
                    this.overallMetrics = response.data.overallMetrics;
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
        downloadServerCustomers(serverIndex) {
            window.location.href = `/api/download/customers/${serverIndex}`;
        },
        downloadAllMetrics() {
            window.location.href = '/api/download/metrics';
        },
        resetSimulation() {
            axios.post('/api/reset')
                .then(() => {
                    this.setupComplete = false;
                    this.isRunning = false;
                    this.currentTime = 0;
                    this.servers = [];
                    this.queues = [];
                    this.serverSummaries = [];
                    this.overallMetrics = null;
                    clearInterval(this.timer);
                });
        },
        getQueueLength(queueIndex) {
            return this.queues[queueIndex] ? this.queues[queueIndex].length : 0;
        },
        formatMetricValue(value) {
            return typeof value === 'number' ? value.toFixed(2) : value;
        }
    },
    created() {
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
