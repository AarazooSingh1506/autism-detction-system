// Eye tracking simulation logic
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('start-tracking');
    const timerDisplay = document.getElementById('timer');
    const resultsDiv = document.getElementById('results');
    const canvas = document.getElementById('gaze-canvas');
    
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Set canvas dimensions
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    let tracking = false;
    let startTime;
    let timer;
    let gazePoints = [];
    
    // Simulated eye tracking data
    function simulateGaze() {
        if (!tracking) return;
        
        // Random gaze point
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        
        // Store point
        gazePoints.push({x, y, timestamp: Date.now()});
        
        // Draw point
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
        ctx.fill();
        
        // Schedule next point
        setTimeout(simulateGaze, 100 + Math.random() * 200);
    }
    
    function startTracking() {
        tracking = true;
        startTime = Date.now();
        gazePoints = [];
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        startButton.disabled = true;
        if (resultsDiv) resultsDiv.style.display = 'none';
        
        // Start simulation
        simulateGaze();
        
        // Start timer
        let seconds = 30;
        timerDisplay.textContent = '00:' + (seconds < 10 ? '0' + seconds : seconds);
        
        timer = setInterval(() => {
            seconds--;
            timerDisplay.textContent = '00:' + (seconds < 10 ? '0' + seconds : seconds);
            
            if (seconds <= 0) {
                clearInterval(timer);
                tracking = false;
                startButton.disabled = false;
                if (resultsDiv) resultsDiv.style.display = 'block';
                
                // Send data to server
                sendGazeData();
            }
        }, 1000);
    }
    
    function sendGazeData() {
        // Process gaze data
        const fixations = Math.floor(gazePoints.length / 10);
        const saccades = Math.floor(gazePoints.length / 5);
        const pupilDilation = (3.5 + Math.random()).toFixed(1);
        
        // Calculate attention areas
        const areas = {
            eyes: 0,
            mouth: 0,
            objects: 0
        };
        
        gazePoints.forEach(point => {
            // Simplified: top-left is eyes, center is mouth, right is objects
            if (point.x < canvas.width/2 && point.y < canvas.height/2) {
                areas.eyes++;
            } else if (point.x > canvas.width/3 && point.x < 2*canvas.width/3 && 
                       point.y > canvas.height/3 && point.y < 2*canvas.height/3) {
                areas.mouth++;
            } else {
                areas.objects++;
            }
        });
        
        // Normalize
        const total = areas.eyes + areas.mouth + areas.objects;
        if (total > 0) {
            areas.eyes = Math.round((areas.eyes / total) * 100);
            areas.mouth = Math.round((areas.mouth / total) * 100);
            areas.objects = Math.round((areas.objects / total) * 100);
        }
        
        // Send to server
        fetch('/simulate-eye-tracking', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fixations: fixations,
                saccades: saccades,
                pupilDilation: pupilDilation,
                attentionAreas: areas
            })
        })
        .then(response => response.json())
        .then(data => {
            // Redirect to results page
            window.location.href = '/results';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
    
    if (startButton) {
        startButton.addEventListener('click', startTracking);
    }
});