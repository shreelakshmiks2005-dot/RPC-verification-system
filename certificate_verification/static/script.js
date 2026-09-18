const fileInput = document.getElementById("certificateFile");
const fileName = document.getElementById("fileName");
const verifyBtn = document.getElementById("verifyBtn");

const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const resultSection = document.getElementById("resultSection");

fileInput.addEventListener("change", function () {
if (this.files.length > 0) {
fileName.textContent = this.files[0].name;
} else {
fileName.textContent = "No file selected";
}
});

verifyBtn.addEventListener("click", async function () {

if (!fileInput.files.length) {
    showError("Please select a certificate first.");
    return;
}

const file = fileInput.files[0];

const formData = new FormData();
formData.append("file", file);

loading.classList.remove("hidden");
errorBox.classList.add("hidden");
resultSection.classList.add("hidden");
verifyBtn.disabled = true;

try {

    const response = await fetch("/certificate/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Certificate verification failed.");
    }

    displayResult(data);

} catch (error) {

    showError(error.message);

} finally {

    loading.classList.add("hidden");
    verifyBtn.disabled = false;
}

});

function displayResult(data) {

resultSection.classList.remove("hidden");

const certificate = data.certificate || {};
const verification = data.verification || {};

document.getElementById("candidateName").textContent =
    certificate.name || "-";

document.getElementById("course").textContent =
    certificate.course || "-";

document.getElementById("issuer").textContent =
    certificate.issuer || "Not available";

document.getElementById("date").textContent =
    certificate.date || "-";

document.getElementById("certificateId").textContent =
    certificate.certificate_id || "Not available";

document.getElementById("fileNameResult").textContent =
    data.filename || "-";


setBadge(
    "nameMatch",
    verification.name_match
);

setBadge(
    "courseMatch",
    verification.course_match
);

setBadge(
    "dateMatch",
    verification.date_match
);

setBadge(
    "idMatch",
    verification.certificate_id_match
);

setBadge(
    "qrVerification",
    verification.verified
);


const verified = verification.verified === true;

const statusCard = document.getElementById("statusCard");
const statusIcon = document.getElementById("statusIcon");
const statusText = document.getElementById("statusText");
const statusMessage = document.getElementById("statusMessage");

if (verified) {

    statusCard.classList.remove("failed");
    statusIcon.textContent = "✓";
    statusText.textContent = "Certificate Verified";
    statusMessage.textContent =
        "The certificate passed the verification checks.";

} else {

    statusCard.classList.add("failed");
    statusIcon.textContent = "!";
    statusText.textContent = "Verification Failed";
    statusMessage.textContent =
        "The certificate could not be fully verified.";
}


let score = calculateScore(
    verification,
    data.database_match
);

document.getElementById("score").textContent = score;


const qrData = document.getElementById("qrData");

if (data.qr_data && data.qr_data.length > 0) {

    qrData.textContent =
        data.qr_data.map(qr => {

            if (qr.data) {
                return qr.data;
            }

            return JSON.stringify(qr);

        }).join("\n");

} else {

    qrData.textContent = "No QR data available.";
}

}

function setBadge(id, value) {

const element = document.getElementById(id);

element.classList.remove("pass", "fail");

if (value === true) {

    element.textContent = "Verified";
    element.classList.add("pass");

} else if (value === false) {

    element.textContent = "Failed";
    element.classList.add("fail");

} else {

    element.textContent = "Not Available";
}


}

function calculateScore(verification, databaseMatch) {

let score = 0;

if (verification.name_match) {
    score += 25;
}

if (verification.course_match) {
    score += 25;
}

if (verification.date_match) {
    score += 20;
}

if (verification.certificate_id_match) {
    score += 20;
}

if (databaseMatch) {
    score += 10;
}

return score;


}

function showError(message) {



}
