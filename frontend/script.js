// Enter para buscar
document.getElementById("serial").addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
    buscar();
  }
});

function buscar() {
  const serial = document.getElementById("serial").value.trim().slice(0, 7);
  const message = document.getElementById("message");

  message.textContent = "";

  if (!serial) {
    messageText = "Informe o código serial.";
    messageColor = "orange";
    showMessage(messageText, messageColor)
    return;
  }

  fetch(`/buscar/${serial}`)
  .then(async response => {
    if (response.status === 404) {
      throw { detail: "Folha de processo não encontrado! Favor, informar Engenharia Industrial." };
    }

    if (!response.ok) {
      let err;
      try {
        err = await response.json();
      } catch {
        err = { detail: "Erro ao buscar o arquivo." };
      }
      throw err;
    }

    return response.blob();
  })
  .then(blob => {
    const pdfUrl = URL.createObjectURL(blob);
    window.open(pdfUrl, "_blank");

    showMessage("Folha de processo encontrada!", "green");

  })
  .catch(err => {
    showMessage(err.detail || "Erro ao buscar o arquivo.", "red");
  })
  .finally(() => {
    document.getElementById("serial").value = "";
    document.getElementById("serial").focus();
  });

}

// ===== Tema Dark / Light com persistência =====
const html = document.documentElement;
const btnTheme = document.getElementById("toggleTheme");

const savedTheme = localStorage.getItem("theme") || "light";
html.setAttribute("data-bs-theme", savedTheme);
btnTheme.textContent = savedTheme === "dark" ? "☀️" : "🌙";

btnTheme.addEventListener("click", () => {
  const newTheme = html.getAttribute("data-bs-theme") === "light" ? "dark" : "light";
  html.setAttribute("data-bs-theme", newTheme);
  localStorage.setItem("theme", newTheme);
  btnTheme.textContent = newTheme === "dark" ? "☀️" : "🌙";
});

// Mensagem

let messageTimeout;

function showMessage(text, color = "black", duration = 7000) {
  const message = document.getElementById("message");

  // Cancela o timeout anterior (se existir)
  clearTimeout(messageTimeout);

  // Substitui a mensagem imediatamente
  message.textContent = text;
  message.style.color = color;

  // Cria um NOVO timeout de 15s
  messageTimeout = setTimeout(() => {
    message.textContent = "";
  }, duration);
}
