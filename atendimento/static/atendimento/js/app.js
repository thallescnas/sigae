function pegarCookieCsrf() {
  const cookies = document.cookie.split(";");
  for (let item of cookies) {
    const cookie = item.trim();
    if (cookie.startsWith("csrftoken=")) {
      return decodeURIComponent(cookie.substring("csrftoken=".length));
    }
  }
  return "";
}

async function enviarRequisicao(url, metodo = "GET", dados = null) {
  const config = {
    method: metodo,
    headers: { "Accept": "application/json" },
    credentials: "same-origin",
  };
  if (metodo !== "GET") {
    config.headers["Content-Type"] = "application/json";
    config.headers["X-CSRFToken"] = pegarCookieCsrf();
    config.body = JSON.stringify(dados || {});
  }
  const resposta = await fetch(url, config);
  const json = await resposta.json();

  if (!resposta.ok || !json.ok) {
    throw new Error(json.error || "Erro ao comunicar com o servidor.");
  }

  return json;
}

function mostrarAviso(texto, ehErro = false) {
  const caixa = document.getElementById("alerta-status");
  caixa.textContent = texto;
  if (ehErro) {
    caixa.className = "alerta-status erro";
  } else caixa.className = "alerta-status";
}

