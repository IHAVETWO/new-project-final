// main.js - Consolidated and enhanced JavaScript for BrightSmile Dental Clinic

// --- Dark Mode Toggle ---
document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('darkModeToggle');
    const body = document.body;
    function setDarkMode(on) {
        if (on) {
            body.classList.add('dark-mode');
            localStorage.setItem('darkMode', '1');
            if (toggle) {
                toggle.innerText = '☀️';
                toggle.setAttribute('aria-label', 'Switch to light mode');
            }
        } else {
            body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', '0');
            if (toggle) {
                toggle.innerText = '🌙';
                toggle.setAttribute('aria-label', 'Switch to dark mode');
            }
        }
    }
    if (toggle) {
        toggle.addEventListener('click', () => setDarkMode(!body.classList.contains('dark-mode')));
        setDarkMode(localStorage.getItem('darkMode') === '1');
    }

    // --- Initialize Bootstrap Tooltips ---
    if (window.bootstrap) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// --- Toast Notification Utility ---
function showToast(title, message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.appendChild(toast);
    document.body.appendChild(container);
    if (window.bootstrap) {
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', function() {
            container.remove();
        });
    }
}

// --- Real-time Updates (Socket.IO) ---
if (window.io) {
    const socket = io();
    socket.on('connect', function() {
        console.log('Connected to server');
        if (window.currentUserId) {
            socket.emit('authenticate', { user_id: window.currentUserId });
        }
    });
    socket.on('authenticated', function(data) {
        if (data.status === 'success' && window.upcomingAppointments) {
            window.upcomingAppointments.forEach(function(appointmentId) {
                socket.emit('join_appointment_room', { appointment_id: appointmentId });
            });
        }
    });
    socket.on('new_notification', function(data) {
        // Update notification badge
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            const currentCount = parseInt(badge.textContent) || 0;
            badge.textContent = currentCount + 1;
        } else {
            const actionBtn = document.querySelector('.action-btn[href*="notifications"]');
            if (actionBtn) {
                const newBadge = document.createElement('span');
                newBadge.className = 'notification-badge';
                newBadge.textContent = '1';
                actionBtn.appendChild(newBadge);
            }
        }
        showToast(data.title, data.message, data.type);
    });
    socket.on('appointment_update', function(data) {
        console.log('Appointment update received:', data);
        location.reload();
    });
    socket.on('system_health', function(data) {
        console.log('System health update:', data);
        // Optionally update system metrics
    });
}

// --- Stats Auto-Update ---
function updateStats() {
    fetch('/api/user-stats')
        .then(response => response.json())
        .then(data => {
            if (document.getElementById('total-appointments'))
                document.getElementById('total-appointments').textContent = data.total_appointments;
            if (document.getElementById('upcoming-appointments'))
                document.getElementById('upcoming-appointments').textContent = data.upcoming_appointments;
            if (document.getElementById('completed-appointments'))
                document.getElementById('completed-appointments').textContent = data.completed_appointments;
            if (document.getElementById('health-score'))
                document.getElementById('health-score').textContent = data.health_score;
            if (document.getElementById('health-score-circle'))
                document.getElementById('health-score-circle').textContent = data.health_score + '%';
        })
        .catch(error => console.error('Error updating stats:', error));
}
if (document.getElementById('total-appointments')) {
    setInterval(updateStats, 30000);
}

// --- Chart.js Analytics (if present) ---
function updateTrendsChart(data) {
    if (window.appointmentTrendsChart) {
        window.appointmentTrendsChart.data.labels = data.dates;
        window.appointmentTrendsChart.data.datasets[0].data = data.counts;
        window.appointmentTrendsChart.data.datasets[1].data = data.moving_average;
        window.appointmentTrendsChart.update();
    }
}
function updateDemographicsChart(data) {
    if (window.demographicsChart) {
        window.demographicsChart.data.labels = Object.keys(data.age_distribution);
        window.demographicsChart.data.datasets[0].data = Object.values(data.age_distribution);
        window.demographicsChart.update();
    }
}
function updateServiceChart(data) {
    if (window.serviceAnalysisChart) {
        const serviceLabels = Object.keys(data.service_statistics);
        const serviceCounts = serviceLabels.map(service => data.service_statistics[service].total_appointments);
        window.serviceAnalysisChart.data.labels = serviceLabels;
        window.serviceAnalysisChart.data.datasets[0].data = serviceCounts;
        window.serviceAnalysisChart.update();
    }
}

// --- Login Page: Password Toggle ---
function togglePassword() {
    var pwd = document.getElementById('password');
    var eye = document.getElementById('eye-icon');
    if (pwd && eye) {
        if (pwd.type === 'password') {
            pwd.type = 'text';
            eye.src = 'https://img.icons8.com/ios-filled/24/2575fc/eye.png';
        } else {
            pwd.type = 'password';
            eye.src = 'https://img.icons8.com/ios-filled/24/cccccc/eye.png';
        }
    }
}
window.togglePassword = togglePassword;

// --- TBC Bank Logo Enhancement ---
document.addEventListener('DOMContentLoaded', function() {
    const tbcLogo = document.querySelector('footer img[alt="TBC Logo"]');
    if (tbcLogo) {
        // Add hover effect
        tbcLogo.style.transition = 'transform 0.2s cubic-bezier(.4,2,.6,1), box-shadow 0.2s';
        tbcLogo.addEventListener('mouseenter', function() {
            tbcLogo.style.transform = 'scale(1.12)';
            tbcLogo.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.15)';
        });
        tbcLogo.addEventListener('mouseleave', function() {
            tbcLogo.style.transform = 'scale(1)';
            tbcLogo.style.boxShadow = 'none';
        });
        // Accessibility: focus effect
        tbcLogo.setAttribute('tabindex', '0');
        tbcLogo.addEventListener('focus', function() {
            tbcLogo.style.transform = 'scale(1.12)';
            tbcLogo.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.15)';
        });
        tbcLogo.addEventListener('blur', function() {
            tbcLogo.style.transform = 'scale(1)';
            tbcLogo.style.boxShadow = 'none';
        });
        // Keyboard: Enter/Space triggers link
        tbcLogo.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                const link = tbcLogo.closest('a');
                if (link) link.click();
            }
        });
    }
}); 