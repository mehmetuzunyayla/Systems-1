function validateForm() {
    let serverAddress = document.getElementById("server_address");
    let username = document.getElementById("username");
    let password = document.getElementById("password");
  
    if (!serverAddress.value) {
      alert("Please enter server address.");
      serverAddress.focus();
      return false;
    }
  
    if (!username.value) {
      alert("Please enter username.");
      username.focus();
      return false;
    }
  
    if (!password.value) {
      alert("Please enter password.");
      password.focus();
      return false;
    }
  
    return true;
  }
  