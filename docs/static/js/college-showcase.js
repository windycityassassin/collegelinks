// College Showcase Interactive Features

class CollegeShowcase {
    constructor() {
        this.isOpen = false;
        this.currentCollege = null;
        this.setupShowcase();
        this.setupMagneticSnap();
    }

    setupShowcase() {
        // Create showcase container
        const showcase = document.createElement('div');
        showcase.id = 'college-showcase';
        showcase.className = 'college-showcase';
        document.body.appendChild(showcase);

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'showcase-close';
        closeBtn.innerHTML = '×';
        closeBtn.onclick = () => this.closeShowcase();
        showcase.appendChild(closeBtn);

        // Content container
        const content = document.createElement('div');
        content.className = 'showcase-content';
        showcase.appendChild(content);

        this.showcase = showcase;
        this.content = content;
    }

    setupMagneticSnap() {
        let markers = document.querySelectorAll('.leaflet-marker-icon');
        markers.forEach(marker => {
            marker.addEventListener('mousemove', (e) => this.handleMagneticSnap(e, marker));
            marker.addEventListener('mouseleave', () => this.resetMarkerPosition(marker));
        });
    }

    handleMagneticSnap(e, marker) {
        const rect = marker.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const mouseX = e.clientX;
        const mouseY = e.clientY;

        const deltaX = mouseX - centerX;
        const deltaY = mouseY - centerY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        const maxDistance = 50; // Maximum distance for magnetic effect

        if (distance < maxDistance) {
            const pull = (maxDistance - distance) / maxDistance;
            const moveX = deltaX * pull * 0.3;
            const moveY = deltaY * pull * 0.3;
            
            marker.style.transform = `translate(${moveX}px, ${moveY}px)`;
            marker.style.transition = 'transform 0.1s ease-out';
        }
    }

    resetMarkerPosition(marker) {
        marker.style.transform = 'translate(0, 0)';
        marker.style.transition = 'transform 0.2s ease-out';
    }

    openShowcase(college) {
        this.currentCollege = college;
        this.isOpen = true;
        this.showcase.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Generate showcase content
        this.content.innerHTML = this.generateShowcaseHTML(college);
        
        // Setup parallax effects
        this.setupParallaxEffects();
        
        // Extract and apply colors
        this.applyDynamicColors(college);
    }

    closeShowcase() {
        this.isOpen = false;
        this.showcase.classList.remove('active');
        document.body.style.overflow = 'auto';
        this.currentCollege = null;
    }

    generateShowcaseHTML(college) {
        return `
            <div class="showcase-header parallax-section">
                <h1>${college.name}</h1>
                <div class="college-type">${college.type}</div>
            </div>

            <div class="showcase-overview parallax-section">
                <div class="overview-content">
                    <h2>Overview</h2>
                    <div class="location-info">
                        <i class="fas fa-map-marker-alt"></i>
                        <p>${college.address}<br>${college.state}</p>
                    </div>
                </div>
            </div>

            ${this.generateAccreditationSection(college)}
            ${this.generateContactSection(college)}
        `;
    }

    generateAccreditationSection(college) {
        if (!college.profile?.accreditation) return '';
        
        return `
            <div class="showcase-accreditation parallax-section">
                <div class="accreditation-content">
                    <h2>Accreditation</h2>
                    <div class="accreditation-grid">
                        <div class="accreditation-item">
                            <div class="value">${college.profile.accreditation.naac_grade}</div>
                            <div class="label">NAAC Grade</div>
                        </div>
                        <div class="accreditation-item">
                            <div class="value">#${college.profile.accreditation.nirf_rank}</div>
                            <div class="label">NIRF Ranking</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    generateContactSection(college) {
        if (!college.profile?.contact) return '';

        return `
            <div class="showcase-contact parallax-section">
                <div class="contact-content">
                    <h2>Contact</h2>
                    <div class="contact-grid">
                        <a href="${college.profile.contact.website}" target="_blank" class="contact-item">
                            <i class="fas fa-globe"></i>
                            <span>Visit Website</span>
                        </a>
                        <a href="mailto:${college.profile.contact.email}" class="contact-item">
                            <i class="fas fa-envelope"></i>
                            <span>${college.profile.contact.email}</span>
                        </a>
                        <div class="contact-item">
                            <i class="fas fa-phone"></i>
                            <span>${college.profile.contact.phone}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    setupParallaxEffects() {
        const sections = document.querySelectorAll('.parallax-section');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, {
            threshold: 0.1
        });

        sections.forEach(section => {
            observer.observe(section);
        });
    }

    async applyDynamicColors(college) {
        // For now, use predefined colors based on college type
        const colors = {
            'Private': '#e74c3c',
            'State': '#3498db',
            'Central': '#2ecc71',
            'Deemed to be Universities': '#9b59b6',
            'Colleges': '#f1c40f'
        };

        const mainColor = colors[college.type] || '#3498db';
        const root = document.documentElement;
        
        root.style.setProperty('--college-primary-color', mainColor);
        root.style.setProperty('--college-secondary-color', this.adjustColor(mainColor, 20));
        root.style.setProperty('--college-text-color', this.isLightColor(mainColor) ? '#000' : '#fff');
    }

    adjustColor(color, amount) {
        return color; // For now, return the same color. Will implement color adjustment later
    }

    isLightColor(color) {
        // Simple check for light/dark colors
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000;
        return brightness > 128;
    }
}

// Export for use in main map script
window.CollegeShowcase = CollegeShowcase;
