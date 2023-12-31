document.addEventListener("DOMContentLoaded", function () {
    // Submit API Key
    let apiKeyForm = document.getElementById('api-key-form');
    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', submitApiKey);
    }

    // Submit URL
    let urlForm = document.getElementById('submit-url');
    if (urlForm) {
        urlForm.addEventListener('submit', submitUrl);
    }

    // Close error popup
    let closePopup = document.getElementById('close-popup');
    if (closePopup) {
        closePopup.addEventListener('click', closeErrorPopup);
    }

    // Share button
    let shareButton = document.getElementById("shareButton");
    if (shareButton) {
        shareButton.addEventListener("click", handleShareButtonClick);
    }
});

let submittedUrl = '';  // Declare at the beginning of your script

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

let effectiveUrl = submittedUrl || (typeof flaskUrl !== 'undefined' ? flaskUrl : ''); // use 'let' instead of 'const'

function submitUrl(event) {
    event.preventDefault();
    const spinner = document.getElementById('loading-spinner');
    spinner.classList.remove('hidden');
    const url = event.target.web_url.value;
    if (!isValidUrl(url)) {
        alert('Please enter a valid URL.');
        return;
    }

    // Save the submitted URL
    submittedUrl = event.target.web_url.value;

    // Update effectiveUrl directly here
    effectiveUrl = submittedUrl || (typeof flaskUrl !== 'undefined' ? flaskUrl : '');

    fetchData(event);
}



async function fetchData(event) {
    const formData = new FormData(event.target);
    const summaryContentElement = document.getElementById('summary-content');
    const spinner = document.getElementById('loading-spinner');
    let response = await fetch('/fetch_text', {
        method: 'POST',
        body: formData
    });
    try {
        const data = await response.json();
        const spinner = document.getElementById('loading-spinner');
        if (data.success) {
            summaryContentElement.innerText = data.summary;
            spinner.classList.add('hidden');
            document.getElementById('summary').classList.remove('hidden'); // Remove the 'hidden' class
        } else {
            summaryContentElement.innerText = 'Error: ' + data.error;
            spinner.classList.add('hidden');
            document.getElementById('summary').classList.remove('hidden'); // Remove the 'hidden' class
        }
    } catch (error) {
        console.error('JSON parsing error:', error);
        summaryContentElement.innerText = 'Failed to parse server response';
        summaryContentElement.classList.remove('hidden'); // Remove the 'hidden' class
    }
}

function closeErrorPopup() {
    const errorPopup = document.getElementById('error-popup');
    const submitUrlButton = document.getElementById('submit-url');

    errorPopup.classList.add('hidden');
    submitUrlButton.disabled = false;
}

async function submitApiKey(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const response = await fetch('/use_api', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();

    if (data.success) {
        alert('API Key submitted successfully');
    } else {
        const errorPopup = document.getElementById('error-popup');
        const submitUrlButton = document.getElementById('submit-url');

        errorPopup.classList.remove('hidden');
        submitUrlButton.disabled = true;
    }
}

// Newly defined function to handle Share button clicks
async function handleShareButtonClick() {
    if (!effectiveUrl) {
        alert('No URL has been submitted yet.');
        return;
    }

    const encodedUrl = encodeURIComponent(effectiveUrl);
    const urlToShare = `${window.location.origin}/summary/${encodedUrl}`;

    try {
        await navigator.clipboard.writeText(urlToShare);
        alert('URL copied to clipboard');
    } catch (err) {
        console.error('Failed to copy URL:', err);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const shareButton = document.getElementById('shareButton');

    // Fallback to flaskUrl if submittedUrl doesn't exist
    const effectiveUrl = submittedUrl || flaskUrl;

    shareButton.addEventListener('click', async () => {
        if (!effectiveUrl) {
            alert('No URL has been submitted yet.'); // Replace with your own notification method
            return;
        }

        const encodedUrl = encodeURIComponent(effectiveUrl);
        const urlToShare = `${window.location.origin}/summary/${encodedUrl}`;

        try {
            await navigator.clipboard.writeText(urlToShare);
            alert('URL copied to clipboard');  // Replace with a more elegant notification
        } catch (err) {
            console.error('Failed to copy URL:', err);
        }
    });
});
