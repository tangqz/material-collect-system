document.addEventListener('DOMContentLoaded', function() {
    const progressBars = document.querySelectorAll('.progress-bar-custom');
    
    progressBars.forEach(bar => {
        const progress = bar.getAttribute('data-progress');
        bar.style.setProperty('--progress-width', `${progress}%`);
    });
});
