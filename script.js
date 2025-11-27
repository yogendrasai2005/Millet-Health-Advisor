// script.js - UPDATED WITH PRODUCT REDIRECTION FEATURE

class MilletAdvisor {
    constructor() {
        this.selectedConcerns = new Set();
        this.apiBase = window.location.origin;
        this.isLoading = false;
        
        // Product URL mapping for milletamma.com
        this.milletProductUrls = {
            'pearl': 'https://milletamma.com/products/bajra-perl-milet-flour-organic-500gm',
            'foxtail': 'https://milletamma.com/products/foxtail-millet-organic-500gm',
            'finger': 'https://milletamma.com/products/ragi-finger-millet-flour-organic-500gm',
            'barnyard': 'https://milletamma.com/products/barnyard-millet-organic-500gm',
            'little': 'https://milletamma.com/products/little-millet-organic-500gm',
            'kodo': 'https://milletamma.com/products/kodo-millet-organic-500gm',
            'proso': 'https://milletamma.com/products/proso-millet-organic-500gm',
            'sorghum': 'https://milletamma.com/products/jowar-sorghum-flour-organic-500gm',
            'bajra': 'https://milletamma.com/products/bajra-perl-milet-flour-organic-500gm',
            'ragi': 'https://milletamma.com/products/ragi-finger-millet-flour-organic-500gm',
            'jowar': 'https://milletamma.com/products/jowar-sorghum-flour-organic-500gm',
            'kangni': 'https://milletamma.com/products/foxtail-millet-organic-500gm',
            'kutki': 'https://milletamma.com/products/little-millet-organic-500gm',
            'sama': 'https://milletamma.com/products/barnyard-millet-organic-500gm',
            'chena': 'https://milletamma.com/products/proso-millet-organic-500gm'
        };
        
        this.init();
    }

    init() {
        this.initTheme();
        this.initEventListeners();
        this.initAnimations();
        this.initScrollAnimations();
    }

    // Theme Management
    initTheme() {
        const savedTheme = localStorage.getItem('millet-theme') || 'dark';
        this.setTheme(savedTheme);
        
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.addEventListener('click', () => {
                const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
                this.setTheme(newTheme);
            });
        }
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('millet-theme', theme);
    }

    // Event Listeners
    initEventListeners() {
        // Health concern cards
        document.querySelectorAll('.concern-card').forEach(card => {
            card.addEventListener('click', (e) => {
                this.toggleConcern(e.currentTarget);
            });
        });

        // Get recommendations button
        const recommendBtn = document.getElementById('getRecommendations');
        if (recommendBtn) {
            recommendBtn.addEventListener('click', () => {
                this.getRecommendations();
            });
        }

        // Download summary button
        const downloadBtn = document.getElementById('downloadSummary');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadSummary();
            });
        }

        // Enter key in textarea
        const textarea = document.getElementById('userQuery');
        if (textarea) {
            textarea.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    this.getRecommendations();
                }
            });
        }

        // Mobile menu toggle
        const mobileToggle = document.querySelector('.nav-mobile-toggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }

        // Navigation smooth scroll
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    // GSAP Animations
    initAnimations() {
        this.animateHero();
        this.animateFloatingCards();
        this.animateStats();
    }

    initScrollAnimations() {
        if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
            gsap.registerPlugin(ScrollTrigger);

            gsap.utils.toArray('.step').forEach((step, i) => {
                gsap.from(step, {
                    scrollTrigger: {
                        trigger: step,
                        start: 'top 80%',
                        toggleActions: 'play none none reverse'
                    },
                    y: 50,
                    opacity: 0,
                    duration: 0.8,
                    delay: i * 0.2
                });
            });

            gsap.utils.toArray('.concern-card').forEach((card, i) => {
                gsap.from(card, {
                    scrollTrigger: {
                        trigger: card,
                        start: 'top 85%',
                        toggleActions: 'play none none reverse'
                    },
                    y: 30,
                    opacity: 0,
                    duration: 0.6,
                    delay: i * 0.1
                });
            });
        }
    }

    animateHero() {
        if (typeof gsap !== 'undefined') {
            gsap.from('.hero-title', {
                duration: 1.2,
                y: 100,
                opacity: 0,
                ease: 'power3.out'
            });

            gsap.from('.hero-subtitle', {
                duration: 1,
                y: 50,
                opacity: 0,
                delay: 0.3,
                ease: 'power2.out'
            });

            gsap.from('.hero-actions', {
                duration: 0.8,
                y: 30,
                opacity: 0,
                delay: 0.6,
                ease: 'power2.out'
            });
        }
    }

    animateFloatingCards() {
        if (typeof gsap !== 'undefined') {
            gsap.to('.floating-card', {
                y: 20,
                duration: 2,
                repeat: -1,
                yoyo: true,
                ease: 'power1.inOut',
                stagger: 0.5
            });
        }
    }

    animateStats() {
        const statElements = document.querySelectorAll('.stat-number');
        statElements.forEach(stat => {
            const target = parseInt(stat.getAttribute('data-count'));
            this.animateCounter(stat, target, 2000);
        });
    }

    animateCounter(element, target, duration) {
        let start = 0;
        const increment = target / (duration / 16);
        const timer = setInterval(() => {
            start += increment;
            if (start >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(start);
            }
        }, 16);
    }

    // Health Concern Management
    toggleConcern(card) {
        const concern = card.dataset.concern;
        
        if (this.selectedConcerns.has(concern)) {
            this.selectedConcerns.delete(concern);
            card.classList.remove('selected');
        } else {
            this.selectedConcerns.add(concern);
            card.classList.add('selected');
            
            if (typeof gsap !== 'undefined') {
                gsap.from(card, {
                    scale: 0.8,
                    duration: 0.3,
                    ease: 'back.out(1.7)'
                });
            }
        }
        
        this.updateSelectedTags();
    }

    removeConcern(concern) {
        this.selectedConcerns.delete(concern);
        const card = document.querySelector(`[data-concern="${concern}"]`);
        if (card) {
            card.classList.remove('selected');
        }
        this.updateSelectedTags();
    }

    updateSelectedTags() {
        const tagsContainer = document.getElementById('selectedConcerns');
        if (!tagsContainer) return;

        tagsContainer.innerHTML = '';
        
        if (this.selectedConcerns.size === 0) {
            tagsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-plus-circle"></i>
                    <span>Select health concerns to get started</span>
                </div>
            `;
            return;
        }
        
        this.selectedConcerns.forEach(concern => {
            const tag = document.createElement('div');
            tag.className = 'selected-tag';
            tag.innerHTML = `
                ${this.getConcernDisplayName(concern)}
                <i class="fas fa-times" onclick="app.removeConcern('${concern}')"></i>
            `;
            tagsContainer.appendChild(tag);
        });

        if (typeof gsap !== 'undefined') {
            gsap.from('.selected-tag', {
                scale: 0,
                duration: 0.3,
                stagger: 0.1,
                ease: 'back.out(1.7)'
            });
        }
    }

    getConcernDisplayName(concern) {
        const names = {
            diabetes: 'Diabetes',
            heart: 'Heart Health',
            digestive: 'Digestive Health',
            anemia: 'Anemia',
            weight: 'Weight Management',
            bones: 'Bone Health',
            gluten: 'Gluten Sensitivity'
        };
        return names[concern] || concern;
    }

    // NEW: Get product URL for millet
    getMilletProductUrl(milletName) {
        const milletLower = milletName.toLowerCase().trim();
        
        // Try exact match first
        if (this.milletProductUrls[milletLower]) {
            return this.milletProductUrls[milletLower];
        }
        
        // Try partial matches
        for (const [key, url] of Object.entries(this.milletProductUrls)) {
            if (milletLower.includes(key) || key.includes(milletLower)) {
                return url;
            }
        }
        
        // Default to millet products page
        return "https://milletamma.com/collections/millet-basket";
    }

    // NEW: Handle product redirection
    redirectToMilletProducts(milletName, event) {
        event.preventDefault();
        
        const productUrl = this.getMilletProductUrl(milletName);
        
        // Show loading state
        const button = event.currentTarget;
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Redirecting...';
        button.disabled = true;
        
        // Open in new tab after a brief delay for UX
        setTimeout(() => {
            window.open(productUrl, '_blank');
            
            // Reset button after a moment
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 1000);
        }, 500);
        
        // Track the click (optional - for analytics)
        this.trackProductClick(milletName, productUrl);
    }

    // NEW: Track product clicks (optional)
    trackProductClick(milletName, productUrl) {
        console.log(`User clicked to view ${milletName} products: ${productUrl}`);
        // Here you could add analytics tracking
        // Example: googleAnalytics.trackEvent('product_click', milletName, productUrl);
    }

    // API Communication - UPDATED
    async getRecommendations() {
        if (this.isLoading) return;

        const userQuery = document.getElementById('userQuery')?.value || '';
        const concerns = Array.from(this.selectedConcerns);

        if (concerns.length === 0) {
            this.showNotification('Please select at least one health concern to get recommendations.', 'warning');
            return;
        }

        this.showLoading();
        this.isLoading = true;

        try {
            const response = await fetch(`${this.apiBase}/api/recommend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    health_concerns: concerns,
                    user_query: userQuery
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data);
            } else {
                throw new Error('Failed to get recommendations from server');
            }
        } catch (error) {
            console.error('Error fetching recommendations:', error);
            this.showNotification(
                'Unable to get recommendations at the moment. Please try again later.', 
                'error'
            );
        } finally {
            this.hideLoading();
            this.isLoading = false;
        }
    }

    // Loading States
    showLoading() {
        const loadingState = document.getElementById('loadingState');
        const steps = loadingState?.querySelectorAll('.step');
        
        if (loadingState) {
            loadingState.classList.remove('hidden');
            
            if (steps) {
                let currentStep = 0;
                const stepInterval = setInterval(() => {
                    if (currentStep > 0) {
                        steps[currentStep - 1].classList.remove('active');
                    }
                    if (currentStep < steps.length) {
                        steps[currentStep].classList.add('active');
                        currentStep++;
                    } else {
                        clearInterval(stepInterval);
                    }
                }, 800);
                
                this.currentStepInterval = stepInterval;
            }

            const progressFill = loadingState.querySelector('.progress-fill');
            if (progressFill && typeof gsap !== 'undefined') {
                gsap.to(progressFill, {
                    width: '100%',
                    duration: 2,
                    ease: 'power2.inOut'
                });
            }
        }
    }

    hideLoading() {
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            loadingState.classList.add('hidden');
            
            if (this.currentStepInterval) {
                clearInterval(this.currentStepInterval);
            }

            const progressFill = loadingState.querySelector('.progress-fill');
            if (progressFill) {
                progressFill.style.width = '0%';
            }
        }
    }

    // Results Display - UPDATED WITH PRODUCT BUTTONS
    displayResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsSummary = document.getElementById('resultsSummary');
        const recommendationsList = document.getElementById('recommendationsList');
        
        if (!resultsSection || !resultsSummary || !recommendationsList) return;

        // Show results section
        resultsSection.classList.remove('hidden');
        
        // Clear any existing content first
        resultsSummary.innerHTML = '';
        recommendationsList.innerHTML = '';

        // Properly set the summary HTML
        resultsSummary.innerHTML = data.summary;

        // Create and append recommendation cards one by one
        data.recommendations.forEach((rec, index) => {
            const cardHtml = this.createRecommendationCard(rec, data.scientific_evidence[rec.name], index);
            const cardElement = document.createElement('div');
            cardElement.innerHTML = cardHtml;
            
            // Ensure the HTML is properly parsed and not escaped
            const benefitsContent = cardElement.querySelector('.benefits-content');
            if (benefitsContent && rec.benefits_summary) {
                benefitsContent.innerHTML = rec.benefits_summary;
            }
            
            recommendationsList.appendChild(cardElement.firstElementChild);
        });

        // Add event listeners to product buttons after they're created
        setTimeout(() => {
            document.querySelectorAll('.product-button').forEach(button => {
                const milletName = button.getAttribute('data-millet');
                button.addEventListener('click', (e) => this.redirectToMilletProducts(milletName, e));
            });
        }, 100);

        // Animate the results section after content is loaded
        setTimeout(() => {
            if (typeof gsap !== 'undefined') {
                gsap.from(resultsSection, {
                    y: 30,
                    opacity: 0,
                    duration: 0.6,
                    ease: 'power2.out'
                });

                gsap.utils.toArray('.millet-card').forEach((card, i) => {
                    gsap.from(card, {
                        y: 40,
                        opacity: 0,
                        duration: 0.5,
                        delay: i * 0.15,
                        ease: 'back.out(1.2)'
                    });
                });
            }

            // Scroll to results with proper offset
            const offset = 100;
            const elementPosition = resultsSection.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }, 100);
    }

    // UPDATED: Create recommendation card with product button
    createRecommendationCard(recommendation, evidence, index) {
        const milletName = this.escapeHtml(recommendation.name);
        const cleanMilletName = milletName.toLowerCase().replace(' millet', '').trim();
        
        return `
            <div class="millet-card" data-index="${index}">
                <div class="card-header">
                    <div class="millet-name">
                        <h3>
                            <i class="fas fa-seedling"></i>
                            ${milletName}
                        </h3>
                        <div class="relevance-badge">
                            ${recommendation.score}% Match
                        </div>
                    </div>
                </div>

                <div class="rating-section">
                    <div class="rating-stars">
                        ${this.generateStars(recommendation.stats.average_rating)}
                    </div>
                    <div class="rating-text">
                        ${recommendation.stats.average_rating}/5 • ${recommendation.stats.total_reviews} reviews
                    </div>
                    <div class="sentiment-indicators">
                        <div class="sentiment-item positive">
                            <i class="fas fa-thumbs-up"></i>
                            <span>${recommendation.stats.positive_percentage}%</span>
                        </div>
                        <div class="sentiment-item neutral">
                            <i class="fas fa-minus"></i>
                            <span>${recommendation.stats.sentiment_distribution.Neutral || 0}</span>
                        </div>
                        <div class="sentiment-item negative">
                            <i class="fas fa-thumbs-down"></i>
                            <span>${recommendation.stats.sentiment_distribution.Negative || 0}</span>
                        </div>
                    </div>
                </div>

                <div class="benefits-section">
                    <div class="section-title">
                        <i class="fas fa-heart"></i>
                        <span>Health Benefits</span>
                    </div>
                    <div class="benefits-content">
                        <!-- Benefits content will be inserted by displayResults -->
                        Loading benefits...
                    </div>
                </div>

                <div class="evidence-section">
                    <div class="section-title">
                        <i class="fas fa-flask"></i>
                        <span>Scientific Evidence</span>
                    </div>
                    <div class="evidence-content">
                        ${this.formatScientificEvidence(evidence)}
                    </div>
                </div>

                <div class="reviews-section">
                    <div class="section-title">
                        <i class="fas fa-users"></i>
                        <span>User Experiences</span>
                    </div>
                    <div class="reviews-content">
                        ${recommendation.sample_reviews.map(review => `
                            <div class="review-item">
                                <i class="fas fa-quote-left"></i>
                                ${this.escapeHtml(review)}
                            </div>
                        `).join('')}
                    </div>
                </div>

                ${recommendation.health_concern_match ? `
                <div class="health-match">
                    ${Object.entries(recommendation.health_concern_match).map(([concern, percentage]) => `
                        <div class="match-item">
                            <div class="match-percentage">${percentage}%</div>
                            <div class="match-label">${this.getConcernDisplayName(concern)}</div>
                        </div>
                    `).join('')}
                </div>
                ` : ''}

                <!-- NEW: Product Section -->
                <div class="product-section">
                    <div class="section-title">
                        <i class="fas fa-shopping-bag"></i>
                        <span>Ready to Try ${milletName}?</span>
                    </div>
                    <div class="product-content">
                        <p>Explore high-quality ${milletName} products from trusted suppliers.</p>
                        <button class="btn btn-primary product-button" data-millet="${cleanMilletName}">
                            <i class="fas fa-external-link-alt"></i>
                            View ${milletName} Products on MilletAmma
                        </button>
                        <p class="product-note">
                            <i class="fas fa-info-circle"></i>
                            You'll be redirected to MilletAmma.com in a new tab
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    // Utility Functions
    generateStars(rating) {
        const fullStars = Math.floor(rating);
        const halfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
        
        let stars = '';
        
        for (let i = 0; i < fullStars; i++) {
            stars += '<i class="fas fa-star"></i>';
        }
        
        if (halfStar) {
            stars += '<i class="fas fa-star-half-alt"></i>';
        }
        
        for (let i = 0; i < emptyStars; i++) {
            stars += '<i class="far fa-star"></i>';
        }
        
        return stars;
    }

    formatScientificEvidence(evidence) {
        if (!evidence || evidence.length === 0) {
            return '<p>Scientific evidence is being analyzed. Please check back soon.</p>';
        }
        
        const items = evidence.slice(0, 2).map(item => {
            const content = item.replace(/^Page \d+: /, '');
            return `<li>${this.escapeHtml(content)}</li>`;
        }).join('');
        
        return `<ul class="bullet-list">${items}</ul>` + (evidence.length > 2 ? 
            '<p><em>... and more scientific evidence available</em></p>' : '');
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    typeWriter(element, text, speed = 30) {
        if (!element || !text) return;
        
        element.innerHTML = '';
        let i = 0;
        
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        
        type();
    }

    // Mobile Menu
    toggleMobileMenu() {
        const navLinks = document.querySelector('.nav-links');
        if (navLinks) {
            navLinks.classList.toggle('active');
        }
    }

    // Download Summary
    downloadSummary() {
        this.showNotification('PDF summary feature coming soon!', 'info');
    }

    // Notifications
    showNotification(message, type = 'info') {
        document.querySelectorAll('.notification').forEach(notification => {
            notification.remove();
        });

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            info: 'info-circle',
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'exclamation-circle'
        };
        
        notification.innerHTML = `
            <i class="fas fa-${icons[type] || 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${this.getNotificationColor(type)};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            max-width: 400px;
            animation: slideInRight 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
        
        notification.addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        });
    }

    getNotificationColor(type) {
        const colors = {
            info: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
            success: 'linear-gradient(135deg, #10b981, #0ea5e9)',
            warning: 'linear-gradient(135deg, #f59e0b, #ef4444)',
            error: 'linear-gradient(135deg, #ef4444, #dc2626)'
        };
        return colors[type] || colors.info;
    }
}

// Global utility functions
function scrollToRecommendations() {
    const section = document.getElementById('recommendations');
    if (section) {
        const offset = 80;
        const elementPosition = section.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

function scrollToHowItWorks() {
    const section = document.getElementById('how-it-works');
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Add CSS for notifications, animations, and product sections
const notificationStyles = `
@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

.notification {
    cursor: pointer;
    transition: transform 0.2s ease;
}

.notification:hover {
    transform: translateY(-2px);
}

/* Product Section Styles */
.product-section {
    margin-top: var(--space-lg);
    padding-top: var(--space-lg);
    border-top: 1px solid var(--color-border);
}

.product-content {
    text-align: center;
    background: linear-gradient(135deg, var(--color-bg-secondary), var(--color-surface));
    padding: var(--space-lg);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
}

.product-content p {
    margin-bottom: var(--space-md);
    color: var(--color-text-secondary);
}

.product-button {
    margin: var(--space-md) 0;
    width: 100%;
    max-width: 400px;
}

.product-note {
    font-size: 0.875rem;
    color: var(--color-text-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-xs);
    margin-top: var(--space-md);
}

@media (max-width: 768px) {
    .notification {
        top: 80px;
        right: 10px;
        left: 10px;
        max-width: none;
    }
    
    .product-content {
        padding: var(--space-md);
    }
}

/* Fix for excessive spacing in results */
.results-section {
    padding-top: 1rem !important;
}

.results-header {
    margin-bottom: 1.5rem !important;
}

.recommendations-list {
    gap: 1.5rem !important;
}

.millet-card {
    margin-bottom: 0 !important;
}
`;

// Inject notification styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MilletAdvisor();
    
    // Add keyboard shortcut help
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === '/') {
            e.preventDefault();
            app.showNotification('💡 Tip: Press Ctrl+Enter in the textarea to quickly get recommendations!', 'info');
        }
    });
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MilletAdvisor;
}