document.addEventListener('DOMContentLoaded', function () {
  const toggleAddress = document.getElementById('toggleAddress');
  const addressField = document.getElementById('addressField');

  // Set the default value of the address from the user's profile
  addressField.dataset.defaultValue = "{{ request.user.userprofile.address|escapejs }}";
  
  // If the checkbox is checked, make the address editable
  toggleAddress.addEventListener('click', function () {
      if (toggleAddress.checked) {
          addressField.removeAttribute('readonly');
          addressField.value = ''; // Clear the address to allow user input
          addressField.focus();
      } else {
          addressField.setAttribute('readonly', true);
          addressField.value = addressField.dataset.defaultValue; // Restore default address
      }
  });

  // If the checkbox is already checked, make the address editable by default
  if (toggleAddress.checked) {
      addressField.removeAttribute('readonly');
      addressField.value = '';
  }
});

  