async function startVoiceRecognition() {
    const outputDiv = document.getElementById('output');
    const loader = document.getElementById('loader');
    
    outputDiv.innerText = "";
    loader.style.display = "block";

    try {
        const response = await fetch('/api/listen', { method: 'POST' });
        const data = await response.json();
        
        loader.style.display = "none";
        outputDiv.innerText = "Recognized: " + data.text;
    } catch (error) {
        loader.style.display = "none";
        outputDiv.innerText = "System Error: Could not connect to server.";
    }
}