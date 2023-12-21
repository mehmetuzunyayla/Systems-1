// file_operations.js

// Function to open the create directory page
function openCreateDirectoryPage() {
    window.location.href = '/create-directory';
}

// Function to create a directory
function createDirectory() {
    console.log('createDirectory function called');
    var directoryName = document.getElementById('directory-name').value;

    // Call the server-side route to create the directory
    fetch('/create-directory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ directoryName: directoryName }),
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the server
        if (data.success) {
            // Redirect to the file list page
            window.location.href = '/files';
        } else {
            // Display an error message (you can customize this part)
            alert('Failed to create the directory. Please try again.');
        }
    });

    // Prevent the form from submitting in the traditional way
    return false;
}

// ... (existing code) ...
