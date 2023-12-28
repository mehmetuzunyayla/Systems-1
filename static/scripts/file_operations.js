function openPath(path) {
    fetch('/open?path=' + encodeURIComponent(path))
      .then(response => {
        if (!response.ok) {
            throw new Error('Server responded with ' + response.status);
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          alert('Error: ' + data.error);
        } else if (data.type === 'file') {
          // Handle file content display
          displayFileContents(path, data.contents);
        } else if (data.type === 'directory') {
          // Update the file list for the directory
          updateFileList(data.contents, data.current_path);
        }
      })
      .catch(error => {
        console.error('Failed to open path:', error);
        alert('Failed to open path: ' + error);
      });
  }
  
  function displayFileContents(filePath, contents) {
    const fileContentsDiv = document.getElementById('file-contents');
    fileContentsDiv.innerHTML = '';  // Clear previous contents
    
    // Display the file name
    const fileName = document.createElement('h2');
    fileName.textContent = 'File: ' + filePath.split('/').pop();
    fileContentsDiv.appendChild(fileName);
    
    // Display the file contents
    const fileContent = document.createElement('pre');
    fileContent.textContent = contents;
    fileContentsDiv.appendChild(fileContent);
  }
  
  function updateFileList(files, currentPath) {
    // Update the current path in the frontend
    document.body.setAttribute('data-home-path', currentPath);
  
    // Update the file list to show the contents of the directory
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = ''; // Clear the current list
    files.forEach(item => {
      const listItem = document.createElement('li');
      const link = document.createElement('a');
      link.href = "#";
      link.className = "file-link";
      link.textContent = item;
      link.setAttribute('data-path', item); // Don't prepend current_path if it's already included.
      link.addEventListener('click', function(event) {
        event.preventDefault(); // Prevent the default link behavior
        openPath(this.getAttribute('data-path'));
      });
      // Create a delete button for each item
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = 'Delete';
      deleteBtn.onclick = function() {
        deleteItem( "/" + item); // Pass the full path to the deleteItem function
      };

      listItem.appendChild(link);
      listItem.appendChild(deleteBtn); // Append the delete button next to the link
      fileList.appendChild(listItem);
    });
  
    // Update the current path display element, if present
    const currentPathDisplay = document.getElementById('current-path-display');
    if (currentPathDisplay) {
      currentPathDisplay.textContent = 'Current Path: ' + currentPath;
    }
  }
  
function createDirectory() {
    const directoryName = document.getElementById('directory-name').value;
    fetch('/create_directory', {
        method: 'POST',
        body: JSON.stringify({ 'directory_name': directoryName }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())  // Always parse the JSON response
    .then(data => {
        if (data.error) {
            // Check for a specific error message
            if (data.error.includes('Directory already exists')) {
                alert('Error: A directory with this name already exists.');
            } else {
                alert('Error: ' + data.error);
            }
        } else {
            alert('Directory created successfully');
            window.location.href = '/home';  // Redirect to the home route
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error);
    });

    return false;  // Prevent default form submission
}
function deleteItem(itemName) {
    if (!confirm('Are you sure you want to delete "' + itemName + '"?')) {
        return; // Do nothing if the user cancels the action
    }
    
    const basePath = document.body.getAttribute('data-home-path');
    const fullPath = basePath + '/' + itemName;
    console.log("Attempting to delete:", fullPath);  // Debugging log

    fetch('/delete_item', {
        method: 'POST',
        body: JSON.stringify({ 'item_path': fullPath }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Item deleted successfully');
            window.location.reload();  // Reload the page to update the list
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error);
    });
}
function createFile() {
    const fileName = document.getElementById('file-name').value;
    const currentPath = document.getElementById('current-path').value;
    console.log("Creating file at path:", currentPath);  // Log for debugging

    fetch('/create_file', {
        method: 'POST',
        body: JSON.stringify({ 'file_name': fileName, 'current_path': currentPath }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('File created successfully');
            window.location.href = '/home';  // Redirect to the home route
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error);
    });

    return false;  // Prevent default form submission
}


// Initialize event listeners once the DOM is fully loaded.
document.addEventListener('DOMContentLoaded', () => {
  // This will apply the click event to initial file links loaded with the page.
  const fileLinks = document.querySelectorAll('.file-link');
  fileLinks.forEach(link => {
    link.addEventListener('click', function(event) {
      event.preventDefault(); // Prevent the default link behavior.
      openPath(this.getAttribute('data-path')); // Call openPath when a file link is clicked.
    });
  });
    // Event listener for the Go to Home button
    document.getElementById('go-home-btn').addEventListener('click', function() {
        window.location.href = '/reset_path';
    });
});
