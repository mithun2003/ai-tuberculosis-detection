document.getElementById("fileInput").addEventListener("change", function () {
    let fileInput = this;
    let preview = document.getElementById("preview");

    if (fileInput.files.length === 0) {
        preview.style.display = "none";
        return;
    }

    let reader = new FileReader();
    reader.onload = function (e) {
        preview.src = e.target.result;
        preview.style.display = "block"; // Show preview image
    };
    reader.readAsDataURL(fileInput.files[0]);
});

function uploadImage() {
    let fileInput = document.getElementById("fileInput");
    let resultText = document.getElementById("result");

    if (fileInput.files.length === 0) {
        alert("Please select an image file.");
        return;
    }

    let formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Send the image to FastAPI backend
    fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        resultText.innerHTML = `TB Probability: <strong>${data.TB_Probability}%</strong>`;
    })
    .catch(error => {
        console.error("Error:", error);
        resultText.innerHTML = "Error processing image.";
    });
}
