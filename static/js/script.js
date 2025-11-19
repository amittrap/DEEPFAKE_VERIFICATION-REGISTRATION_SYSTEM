document.getElementById('imageForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const fileInput = document.getElementById('imageInput');
    const resultText = document.getElementById('resultText');
    const hashText = document.getElementById('hashText');
    const button = document.getElementById('uploadBtn');

    if (fileInput.files.length === 0) {
        alert("Please select an image file.");
        return;
    }

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    // UI feedback
    resultText.textContent = 'Analyzing image...';
    resultText.className = 'pending';
    hashText.textContent = '';
    button.disabled = true;
    button.textContent = "Processing...";

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        button.disabled = false;
        button.textContent = "Verify Image";

        if (result.error) {
            resultText.textContent = "Error: " + result.error;
            resultText.className = "fake";
        } else {
            const status = result.status;
            const hash = result.hash;

            hashText.textContent = `Image Hash: ${hash}`;

            if (status === 'fake') {
                resultText.textContent = "⚠️ Image is FAKE (Deepfake detected)";
                resultText.className = "fake";
            } else if (status === 'real-verified') {
                resultText.textContent = "✅ Image is REAL and already verified on Blockchain.";
                resultText.className = "verified";
            } else if (status === 'real-new') {
                resultText.textContent = "✅ Image is REAL and has been stored on Blockchain.";
                resultText.className = "verified";
            }
        }
    } catch (error) {
        console.error(error);
        resultText.textContent = "Error occurred during verification.";
        resultText.className = "fake";
        button.disabled = false;
        button.textContent = "Verify Image";
    }
});
