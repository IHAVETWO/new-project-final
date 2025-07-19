// Inject admin/analytics CSS if on an admin page
(function() {
  const adminPaths = [
    '/admin',
    '/admin/users',
    '/admin/appointments',
    '/admin/analytics-dashboard',
    '/admin/advanced-analytics',
    '/admin/performance-report',
    '/admin/export-report',
    '/admin/send-reminders',
    '/smart-appointment-scheduler'
  ];
  const isAdminPage = adminPaths.some(path => window.location.pathname.startsWith(path));
  if (isAdminPage) {
    const style = document.createElement('style');
    style.textContent = `
      body {
        background: linear-gradient(135deg, #0f2027, #2c5364, #f8ffae);
        min-height: 100vh;
        margin: 0;
        font-family: 'Inter', Arial, sans-serif;
        color: #fff;
      }
      .container {
        max-width: 1000px;
        margin: 40px auto;
        background: rgba(255,255,255,0.08);
        border-radius: 24px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        padding: 40px 32px 32px 32px;
      }
      h1, h2, h3, h4, h5 {
        font-family: 'Orbitron', 'Inter', Arial, sans-serif;
        letter-spacing: 2px;
        color: #b2fefa;
        text-shadow: 0 2px 16px #0f2027;
      }
      .admin-nav ul {
        display: flex;
        gap: 24px;
        justify-content: center;
        padding: 0;
        list-style: none;
        margin-bottom: 32px;
      }
      .admin-nav a {
        display: inline-block;
        padding: 12px 28px;
        font-size: 1.1rem;
        font-weight: bold;
        color: #fff;
        background: linear-gradient(90deg, #b2fefa 0%, #0ed2f7 100%);
        border: none;
        border-radius: 32px;
        box-shadow: 0 4px 24px #0ed2f7aa;
        text-decoration: none;
        transition: background 0.3s, transform 0.2s;
      }
      .admin-nav a:hover {
        background: linear-gradient(90deg, #0ed2f7 0%, #b2fefa 100%);
        color: #0f2027;
        transform: scale(1.05);
      }
      .admin-content {
        text-align: center;
        margin-top: 32px;
      }
      .admin-content p {
        font-size: 1.2rem;
        color: #f8ffae;
      }
      .fab {
        position: fixed;
        bottom: 32px;
        right: 32px;
        background: linear-gradient(90deg, #b2fefa 0%, #0ed2f7 100%);
        color: #0f2027;
        border-radius: 50%;
        width: 64px;
        height: 64px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        box-shadow: 0 4px 24px #0ed2f7aa;
        text-decoration: none;
        transition: background 0.3s, transform 0.2s;
      }
      .fab:hover {
        background: linear-gradient(90deg, #0ed2f7 0%, #b2fefa 100%);
        color: #fff;
        transform: scale(1.08);
      }
      .table {
        background: #fff2;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 2px 12px #0ed2f755;
      }
      .table th {
        background: linear-gradient(90deg, #b2fefa 0%, #0ed2f7 100%);
        color: #0f2027;
        font-size: 1.1rem;
      }
      .table td {
        color: #fff;
        background: rgba(255,255,255,0.05);
      }
      .table tr:nth-child(even) td {
        background: rgba(255,255,255,0.12);
      }
      .text-muted {
        color: #f8ffae !important;
      }
    `;
    document.head.appendChild(style);
  }
})(); 