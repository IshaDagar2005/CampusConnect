// CampusConnect - Interactive Scripts (Zero Emojis)

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Menu Toggle
  var menuToggle = document.getElementById('menuToggle');
  var navMenu = document.getElementById('navMenu');

  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      navMenu.classList.toggle('nav-open');
    });

    // Close menu when clicking outside
    document.addEventListener('click', function (e) {
      if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
        navMenu.classList.remove('nav-open');
      }
    });
  }

  // 2. Flash Message Auto-Dismissal
  var flashMessages = document.querySelectorAll('.flash');
  flashMessages.forEach(function (msg) {
    setTimeout(function () {
      msg.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      msg.style.opacity = '0';
      msg.style.transform = 'translateY(-6px)';
      setTimeout(function () {
        if (msg.parentNode) {
          msg.parentNode.removeChild(msg);
        }
      }, 400);
    }, 5000);
  });

  // 3. Client-side File Validation for Submissions
  var fileInputs = document.querySelectorAll('input[type="file"][data-max-size]');
  fileInputs.forEach(function (input) {
    input.addEventListener('change', function () {
      var file = this.files[0];
      if (!file) return;

      var maxBytes = parseInt(this.getAttribute('data-max-size'), 10) || (12 * 1024 * 1024);
      if (file.size > maxBytes) {
        alert('File size exceeds the 12 MB limit. Please select a smaller file.');
        this.value = '';
        return;
      }

      var allowedExtensions = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'zip', 'txt', 'png', 'jpg', 'jpeg'];
      var extension = file.name.split('.').pop().toLowerCase();
      if (allowedExtensions.indexOf(extension) === -1) {
        alert('Unsupported file type. Allowed formats: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, ZIP, TXT, PNG, JPG.');
        this.value = '';
        return;
      }
    });
  });

  // 4. Confirmation on delete buttons
  var deleteForms = document.querySelectorAll('form[data-confirm]');
  deleteForms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      var msg = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
});
