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
  
  const filteredFiles = files.filter(item => !item.startsWith('.'));

  filteredFiles.forEach(item => {
      const listItem = document.createElement('li');
      listItem.className = 'file-item';

      const link = document.createElement('a');
      link.href = "#";
      link.className = "file-link";
      link.textContent = item;
      link.setAttribute('data-path', "/" + item); // Make sure to include the current_path
      link.addEventListener('click', function(event) {
          event.preventDefault(); // Prevent the default link behavior
          openPath(this.getAttribute('data-path'));
      });

      // Create context menu container
      const contextMenu = document.createElement('div');
      contextMenu.className = 'context-menu';

      // Create context menu button
      const menuButton = document.createElement('button');
      menuButton.className = 'context-menu-button';
      menuButton.textContent = '...';
      menuButton.onclick = function(event) {
          showContextMenu(event);
      };

      // Create context menu content
      const menuContent = document.createElement('div');
      menuContent.className = 'menu-content';
      menuContent.style.display = 'none';

      // Create delete button
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = 'Delete';
      deleteBtn.onclick = function() {
          deleteItem(item); // Pass the full path to the deleteItem function
      };

      // Create copy button
      const copyBtn = document.createElement('button');
      copyBtn.textContent = 'Copy';
      copyBtn.onclick = function() {
          copyItem(item); // Pass the full path to the copyItem function
      };

      // Create move button
      const moveBtn = document.createElement('button');
      moveBtn.textContent = 'Move';
      moveBtn.onclick = function() {
          moveItem(item); // Pass the full path to the moveItem function
      };

      // Create edit button
      const editBtn = document.createElement('button');
      editBtn.textContent = 'Edit File';
      editBtn.onclick = function() {
          editFile(item); // Pass the full path to the editFile function
      };

      // Append buttons to menu content
      menuContent.appendChild(deleteBtn);
      menuContent.appendChild(copyBtn);
      menuContent.appendChild(moveBtn);
      menuContent.appendChild(editBtn);

      // Append menu button and content to context menu container
      contextMenu.appendChild(menuButton);
      contextMenu.appendChild(menuContent);

      // Append link and context menu to list item
      listItem.appendChild(link);
      listItem.appendChild(contextMenu);

      // Append list item to file list
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

function showContextMenu(event) {
  // Prevent the default right-click context menu from appearing
  event.preventDefault();
  
  // Close any other open menus
  document.querySelectorAll('.menu-content').forEach(function(menu) {
    menu.style.display = 'none';
  });

  // Find the clicked menu content and display it
  const contextMenu = event.target.nextElementSibling;
  contextMenu.style.display = 'block';
  
  // Position the menu at the cursor's location
  contextMenu.style.left = event.pageX + 'px';
  contextMenu.style.top = event.pageY + 'px';
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

function resetSessionPath() {
    return fetch('/reset_session_path', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Session path reset to default:', data.default_path);
            return data.default_path;
        } else {
            console.error('Error resetting session path:', data.error);
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Failed to reset session path:', error);
        throw error;
    });
}

function copyItem(filename) {
  const currentPath = document.body.getAttribute('data-home-path');
  const filePath = currentPath + '/' + filename;
  const destinationPath = prompt('Enter the destination path:', filePath);
  if (destinationPath) {
      fetch('/copy_item', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({ source: filePath, destination: destinationPath })
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              alert('Item copied successfully');
              resetSessionPath()
                .then(() => {
                    // Then open the destination path
                    openPath(data.destination_path);
                })     
                .catch(error => console.error('Error resetting session path:', error));       
           } else {
              alert('Error copying item: ' + data.error);
          }
      })
      .catch(error => {
        alert('Failed to send copy request: ' + error);
      });
  } else {
      console.log('Copy operation cancelled by user.');
  }
}

function moveItem(filename) {
  const currentPath = document.body.getAttribute('data-home-path');
  const filePath = currentPath + '/' + filename;
  const destinationPath = prompt('Enter the destination path:', filePath);

  if (destinationPath) {
      fetch('/move_item', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({ source: filePath, destination: destinationPath })
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              alert('Item moved successfully');
              resetSessionPath()
                .then(() => {
                    // Then open the destination path
                    openPath(data.destination_path);
                })     
                .catch(error => console.error('Error resetting session path:', error));       

          } else {
              alert('Error moving item: ' + data.error);
          }
      })
      .catch(error => alert('Failed to send move request: ' + error));
  } else {
      console.log('Move operation cancelled by user.');
  }
}

// Close the context menu when clicking outside of it
window.addEventListener('click', function(e) {
  if (!e.target.matches('.context-menu button')) {
    var menus = document.getElementsByClassName("menu-content");
    for (var i = 0; i < menus.length; i++) {
      var openMenu = menus[i];
      if (openMenu.style.display === 'block') {
        openMenu.style.display = 'none';
      }
    }
  }
});

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
