// s3ui-app.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application when the DOM is fully loaded
    initializeApp();
});

function initializeApp() {
    // Set up event listeners
    setupEventListeners();
    
    // Load initial directory contents
    loadDirectoryContents('/');
}

function setupEventListeners() {
    // Create Directory button
    document.getElementById('create-directory').addEventListener('click', createDirectory);

    // Search button
    document.getElementById('search-button').addEventListener('click', performSearch);

    // File search input (for real-time search, if desired)
    document.getElementById('file-search').addEventListener('input', performSearch);

    // Pagination buttons
    document.getElementById('prev-page').addEventListener('click', () => changePage('prev'));
    document.getElementById('next-page').addEventListener('click', () => changePage('next'));
}

async function loadDirectoryContents(path) {
    try {
        const response = await fetch(`/api/list-objects?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        renderFileList(data.objects);
        updateBreadcrumb(path);
    } catch (error) {
        console.error('Error loading directory contents:', error);
        // Display error message to user
    }
}

function renderFileList(objects) {
    const fileListElement = document.querySelector('.file-list tbody');
    fileListElement.innerHTML = ''; // Clear existing content

    objects.forEach(object => {
        const row = createFileListRow(object);
        fileListElement.appendChild(row);
    });
}

function createFileListRow(object) {
    const row = document.createElement('tr');
    
    // Name column
    const nameCell = document.createElement('td');
    const icon = document.createElement('img');
    icon.src = object.isDirectory ? 'icons/folder-icon.png' : 'icons/file-icon.png';
    icon.alt = object.isDirectory ? 'Folder' : 'File';
    const nameLink = document.createElement('a');
    nameLink.href = '#';
    nameLink.textContent = object.name;
    nameLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (object.isDirectory) {
            loadDirectoryContents(object.path);
        } else {
            // Handle file click (e.g., download or preview)
        }
    });
    nameCell.appendChild(icon);
    nameCell.appendChild(nameLink);
    row.appendChild(nameCell);

    // Last Modified column
    const modifiedCell = document.createElement('td');
    modifiedCell.textContent = new Date(object.lastModified).toLocaleString();
    row.appendChild(modifiedCell);

    // Size column
    const sizeCell = document.createElement('td');
    sizeCell.textContent = object.isDirectory ? '-' : formatFileSize(object.size);
    row.appendChild(sizeCell);

    // Actions column
    const actionsCell = document.createElement('td');
    ['rename', 'delete', 'move'].forEach(action => {
        const button = document.createElement('button');
        button.className = 'action-btn';
        button.title = action.charAt(0).toUpperCase() + action.slice(1);
        const icon = document.createElement('img');
        icon.src = `icons/${action}-icon.png`;
        icon.alt = button.title;
        button.appendChild(icon);
        button.addEventListener('click', () => handleAction(action, object));
        actionsCell.appendChild(button);
    });
    row.appendChild(actionsCell);

    return row;
}

function updateBreadcrumb(path) {
    const breadcrumb = document.querySelector('.breadcrumb');
    breadcrumb.innerHTML = '';
    
    const pathParts = path.split('/').filter(Boolean);
    let currentPath = '';

    const homeLi = document.createElement('li');
    homeLi.className = 'breadcrumb-item';
    const homeLink = document.createElement('a');
    homeLink.href = '#';
    homeLink.textContent = 'Home';
    homeLink.addEventListener('click', (e) => {
        e.preventDefault();
        loadDirectoryContents('/');
    });
    homeLi.appendChild(homeLink);
    breadcrumb.appendChild(homeLi);

    pathParts.forEach((part, index) => {
        currentPath += '/' + part;
        const li = document.createElement('li');
        li.className = 'breadcrumb-item';
        if (index === pathParts.length - 1) {
            li.classList.add('active');
            li.textContent = part;
        } else {
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = part;
            link.addEventListener('click', (e) => {
                e.preventDefault();
                loadDirectoryContents(currentPath);
            });
            li.appendChild(link);
        }
        breadcrumb.appendChild(li);
    });
}

function createDirectory() {
    const directoryName = prompt('Enter new directory name:');
    if (directoryName) {
        // Call API to create directory
        console.log('Creating directory:', directoryName);
        // After successful creation, reload current directory
    }
}

function performSearch() {
    const searchTerm = document.getElementById('file-search').value;
    // Call API with search term and update file list
    console.log('Searching for:', searchTerm);
}

function changePage(direction) {
    // Implement pagination logic
    console.log('Changing page:', direction);
}

function handleAction(action, object) {
    switch (action) {
        case 'rename':
            const newName = prompt(`Enter new name for ${object.name}:`);
            if (newName) {
                // Call API to rename
                console.log('Renaming', object.name, 'to', newName);
            }
            break;
        case 'delete':
            if (confirm(`Are you sure you want to delete ${object.name}?`)) {
                // Call API to delete
                console.log('Deleting', object.name);
            }
            break;
        case 'move':
            const newPath = prompt(`Enter new path for ${object.name}:`);
            if (newPath) {
                // Call API to move
                console.log('Moving', object.name, 'to', newPath);
            }
            break;
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Add more functions as needed for additional functionality
