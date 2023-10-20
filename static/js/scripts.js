
// Show the error popup and disable the submit URL button
const errorPopup = document.getElementById('error-popup');
const submitUrlButton = document.getElementById('submit-url');
document.getElementById('close-popup').addEventListener('click', function () {
    errorPopup.classList.add('hidden');
    submitUrlButton.disabled = false; // Re-enable the submit URL button
});

async function submitApiKey(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const response = await fetch('/use_api', {
        method: 'POST',
        body: formData,
    });
    const data = await response.json();
    if (data.success) {
        alert('API Key submitted successfully');
    } else {
        // Show the error popup
        errorPopup.classList.remove('hidden');
        submitUrlButton.disabled = true; // Disable the submit URL button
    }
}

async function submitUrl(event) {
    event.preventDefault();
    const web_url = event.target.web_url.value;
    if (!isValidUrl(web_url)) {
        alert('Please enter a valid URL');
        return;
    }
    document.getElementById('summary').innerHTML = '<div class="loader"></div>';  // Show loading animation
    document.getElementById('summary').classList.remove('hidden');
    const formData = new FormData(event.target);
    const response = await fetch('/fetch_text', {
        method: 'POST',
        body: formData,
    });

    try {
        const data = await response.json();
        if (data.success) {
            document.getElementById('summary').innerText = data.summary;
        } else {
            document.getElementById('summary').innerText = 'Error: ' + data.error;
        }
    } catch (error) {
        console.error('JSON parsing error:', error);
        document.getElementById('summary').innerText = 'Failed to parse server response';
    }
    
    const data = await response.json();
    if (data.success) {
        document.getElementById('summary').innerText = data.summary;
    } else {
        document.getElementById('summary').innerText = 'Failed to retrieve text: ' + (data.error || 'Unknown error');
    }
}

function isValidUrl(string) {
    try {
        new URL(string);
    } catch (_) {
        return false;
    }
    return true;
}
