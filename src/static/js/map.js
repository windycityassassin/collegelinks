// Initialize the map
const map = L.map('map').setView([39.8283, -98.5795], 4); // Center of USA

// Add the OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Store markers
let markers = [];

// Fetch colleges data
async function fetchColleges() {
    try {
        const response = await fetch('/api/colleges');
        const colleges = await response.json();
        displayColleges(colleges);
    } catch (error) {
        console.error('Error fetching colleges:', error);
    }
}

// Display colleges on the map and in the sidebar
function displayColleges(colleges) {
    const collegeList = document.getElementById('college-list');
    collegeList.innerHTML = '';

    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    colleges.forEach(college => {
        // Add marker to map
        const marker = L.marker([college.latitude, college.longitude])
            .bindPopup(`<b>${college.name}</b><br>${college.address}`);
        markers.push(marker);
        marker.addTo(map);

        // Add to sidebar list
        const collegeItem = document.createElement('div');
        collegeItem.className = 'college-item';
        collegeItem.innerHTML = `
            <h3>${college.name}</h3>
            <p>${college.address}</p>
        `;
        collegeItem.addEventListener('click', () => {
            map.setView([college.latitude, college.longitude], 15);
            marker.openPopup();
        });
        collegeList.appendChild(collegeItem);
    });
}

// Search functionality
const searchInput = document.getElementById('college-search');
searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const collegeItems = document.querySelectorAll('.college-item');
    
    collegeItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
});

// Load colleges when the page loads
fetchColleges();
