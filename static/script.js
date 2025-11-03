let html5QrCode;
const qrModal = new bootstrap.Modal(document.getElementById("qrModal"));

// ------------------ QR SCANNER CONTROL ------------------ //
function startScanner() {
  const readerElem = document.getElementById("reader");
  readerElem.innerHTML = ""; // clear any previous instance
  qrModal.show();

  html5QrCode = new Html5Qrcode("reader");

  html5QrCode
    .start(
      { facingMode: "environment" },
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        document.getElementById("item_code").value = decodedText;
        fetch(`/get_item_name/${decodedText}`)
          .then((res) => res.json())
          .then((data) => {
            document.getElementById("item_name").value = data.item_name || "";
          })
          .catch(() => {});
        stopScanner();
      },
      () => {}
    )
    .catch((err) => {
      alert("Camera access denied or unavailable: " + err);
    });
}

function stopScanner() {
  if (html5QrCode) {
    html5QrCode
      .stop()
      .then(() => html5QrCode.clear())
      .catch(() => {});
  }
  qrModal.hide();
}

// Event Listeners for scanner controls
document.getElementById("startBtn").addEventListener("click", startScanner);
document.getElementById("stopBtn").addEventListener("click", stopScanner);
document.getElementById("closeModal").addEventListener("click", stopScanner);

// ------------------ AUTO-FETCH PROFESSOR DETAILS ------------------ //
document.getElementById("professor_id").addEventListener("input", function () {
  const id = this.value.trim();

  if (!id) {
    document.getElementById("professor_name").value = "";
    document.getElementById("department").value = "";
    return;
  }

  fetch(`/get_professor/${id}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.found) {
        document.getElementById("professor_name").value = data.name;
        document.getElementById("department").value = data.department;
      } else {
        document.getElementById("professor_name").value = "";
        document.getElementById("department").value = "";
      }
    })
    .catch(() => {});
});

// ------------------ AUTO-FETCH ITEM NAME ------------------ //
document.getElementById("item_code").addEventListener("input", function () {
  const code = this.value.trim();
  if (!code) {
    document.getElementById("item_name").value = "";
    return;
  }

  fetch(`/get_item_name/${code}`)
    .then((res) => res.json())
    .then((data) => {
      document.getElementById("item_name").value = data.item_name || "";
    })
    .catch(() => {});
});

// ------------------ FORM SUBMISSION (Issue/Return) ------------------ //
document.getElementById("issueForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const payload = {
    professor_id: document.getElementById("professor_id").value.trim(),
    professor_name: document.getElementById("professor_name").value.trim(),
    department: document.getElementById("department").value.trim(),
    item_code: document.getElementById("item_code").value.trim(),
    action: document.getElementById("action").value,
  };

  // Validation check
  if (
    !payload.professor_id ||
    !payload.professor_name ||
    !payload.department ||
    !payload.item_code
  ) {
    showStatus("⚠️ Please fill all required fields.", "red");
    return;
  }

  try {
    const res = await fetch("/log_item", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const text = await res.text(); // read response as text first
    let data;

    try {
      data = JSON.parse(text); // try parsing JSON
    } catch (err) {
      console.error("Server returned non-JSON:", text);
      showStatus("⚠️ Unexpected response from server.", "red");
      return;
    }

    // Handle valid JSON response
    showStatus(data.message || "✅ Action completed.", data.status === "error" ? "red" : "green");

    if (data.status === "success") {
      document.getElementById("item_code").value = "";
      document.getElementById("item_name").value = "";
    }
  } catch (err) {
    showStatus("❌ Network error: " + err, "red");
  }
});

// ------------------ STATUS HELPER ------------------ //
function showStatus(message, color) {
  const statusElem = document.getElementById("status");
  statusElem.innerText = message;
  statusElem.style.color = color;
}

// ------------------ OPTIONAL: CLEAR ALL FIELDS ------------------ //
function clearAllFields() {
  document.getElementById("professor_id").value = "";
  document.getElementById("professor_name").value = "";
  document.getElementById("department").value = "";
  document.getElementById("item_code").value = "";
  document.getElementById("item_name").value = "";
  document.getElementById("status").innerText = "";
}
