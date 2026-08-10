// Enter para buscar
document.getElementById("serial").addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
    buscar();
  }
});

fetch("/api/me")
  .then(response => {
    if (response.status === 401) {
      window.location.assign("/login");
      return null;
    }
    if (!response.ok) {
      throw new Error("Não foi possível identificar o usuário.");
    }
    return response.json();
  })
  .then(user => {
    if (!user) return;
    document.getElementById("currentUser").textContent =
      user.name || user.preferred_username || "Usuário autenticado";
  })
  .catch(() => showMessage("Não foi possível identificar o usuário.", "red"));

function buscar() {
  const serial = document.getElementById("serial").value.trim().slice(0, 7);
  const message = document.getElementById("message");

  message.textContent = "";

  if (!serial) {
    showMessage("Informe o código serial.", "orange");
    return;
  }

  fetch(`/buscar/${serial}`)
    .then(async response => {
      if (response.status === 401) {
        window.location.assign(`/login?return_to=${encodeURIComponent(window.location.pathname)}`);
        return null;
      }

      if (response.status === 403) {
        throw { detail: "Seu usuário não possui a permissão viewer." };
      }

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

      // Se chegou aqui, o backend respondeu um PDF válido.
      // Agora abrimos diretamente o endpoint em uma nova aba.
      if (response) {
        window.open(`/buscar/${serial}`, "_blank");
      }

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
