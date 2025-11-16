document.addEventListener("DOMContentLoaded", function () {
  const alerts = document.querySelectorAll(".auto-dismiss");

  alerts.forEach(function (alert) {
    const timeout = alert.getAttribute("data-timeout") || 3000;

    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, parseInt(timeout));
  });

  const alertList = document.querySelectorAll(".alert");
  alertList.forEach(function (alert) {
    alert.addEventListener("closed.bs.alert", function () {
      console.log("Alerta cerrada");
    });
  });
});
