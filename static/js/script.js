// General utility functions
document.addEventListener('DOMContentLoaded', function() {
    // Add any common JavaScript functionality here
    console.log("Application loaded");
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});