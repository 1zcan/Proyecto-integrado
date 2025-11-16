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

document.addEventListener('DOMContentLoaded', function() {
    
    const fileInput = document.getElementById('{{ foto_form.foto.id_for_label }}');
    const previewImage = document.getElementById('foto-preview');

   
    fileInput.addEventListener('change', function() {
       
        if (fileInput.files && fileInput.files[0]) {
            
            const reader = new FileReader();   
            reader.onload = function(e) {
              
                previewImage.src = e.target.result;
            }
            
            reader.readAsDataURL(fileInput.files[0]);
        }
    });
});