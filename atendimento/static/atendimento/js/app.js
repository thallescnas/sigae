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

async function executarAcao(
  url,
  dados = {},
  mensagemPadrao = "Operação concluída!",
) {
  try {
    const resposta = await enviarRequisicao(url, "POST", dados);
    atualizarTela(resposta.snapshot);
    mostrarAviso(resposta.message || mensagemPadrao);
  } catch (erro) {
    mostrarAviso(erro.message, true);
  }
}

function atualizarTela(snapshot) {
  if (!snapshot) return;

  const contadores = snapshot.counts || {};
  document.getElementById("count-aguardando").textContent =
    contadores.aguardando || 0;
  document.getElementById("count-atendimento").textContent =
    contadores.em_atendimento || 0;
  document.getElementById("count-concluido").textContent =
    contadores.concluido || 0;
  document.getElementById("count-cancelado").textContent =
    contadores.cancelado || 0;
  document.getElementById("count-med-livres").textContent =
    contadores.medicos_disponiveis || 0;
  document.getElementById("count-med-ocupados").textContent =
    contadores.medicos_ocupados || 0;

  const proxPaciente = snapshot.next_patient;
  document.getElementById("preview-paciente").textContent = proxPaciente
    ? `#${proxPaciente.id} ${proxPaciente.name} (${proxPaciente.priority_label} - ${proxPaciente.arrival_time})`
    : "Fila vazia";

  const proxMedico = snapshot.next_doctor;
  document.getElementById("preview-medico").textContent = proxMedico
    ? `${proxMedico.name} (${proxMedico.completed_count} concluídos)`
    : "Nenhum disponível";

  const fila = snapshot.waiting_priority || [];
  const caixaFila = document.getElementById("lista-fila-prioridade");
  if (fila.length === 0) {
    caixaFila.innerHTML = `<p class="vazio">Nenhum paciente aguardando na fila.</p>`;
  } else {
    caixaFila.innerHTML = fila
      .map(
        (paciente) => `
      <div class="card-paciente">
        <div>
          <strong>#${paciente.id} ${paciente.name}</strong><br>
          <small>Chegada: ${paciente.arrival_time}</small>
        </div>
        <span class="badge badge-${paciente.priority}">${paciente.priority_label}</span>
        <div class="card-acoes">
          <select onchange="executarAcao('/api/patients/${paciente.id}/priority/', { priority: Number(this.value) })">
            <option value="1" ${paciente.priority === 1 ? "selected" : ""}>1 - Emergência</option>
            <option value="2" ${paciente.priority === 2 ? "selected" : ""}>2 - Muito urgente</option>
            <option value="3" ${paciente.priority === 3 ? "selected" : ""}>3 - Urgente</option>
            <option value="4" ${paciente.priority === 4 ? "selected" : ""}>4 - Pouco urgente</option>
            <option value="5" ${paciente.priority === 5 ? "selected" : ""}>5 - Não urgente</option>
          </select>
          <button type="button" class="btn-cancelar" onclick="executarAcao('/api/patients/${paciente.id}/cancel/')">Cancelar</button>
        </div>
      </div>
    `,
      )
      .join("");
  }

  const cronologica = snapshot.waiting_chronological || [];
  const caixaCronologica = document.getElementById("lista-cronologica");
  if (cronologica.length === 0) {
    caixaCronologica.innerHTML = `<p class="vazio">Sem registros cronológicos em espera.</p>`;
  } else {
    caixaCronologica.innerHTML = cronologica
      .map(
        (paciente) => `
      <div class="card-paciente">
        <span><strong>${paciente.arrival_time}</strong> — #${paciente.id} ${paciente.name}</span>
        <span class="badge badge-${paciente.priority}">${paciente.priority_label}</span>
      </div>
    `,
      )
      .join("");
  }

  const todosPacientes = snapshot.all_patients || [];
  const caixaTodos = document.getElementById("lista-todos-pacientes");
  if (todosPacientes.length === 0) {
    caixaTodos.innerHTML = `<p class="vazio">Nenhum paciente cadastrado.</p>`;
  } else {
    caixaTodos.innerHTML = todosPacientes
      .map(
        (paciente) => `
      <div class="card-paciente">
        <div>
          <strong>#${paciente.id} ${paciente.name}</strong><br>
          <small>Chegada: ${paciente.arrival_time} • ${paciente.status}</small>
        </div>
        <span class="badge badge-${paciente.priority}">${paciente.priority_label}</span>
      </div>
    `,
      )
      .join("");
  }

  const ativos = snapshot.active_attendances || [];
  const caixaAtivos = document.getElementById("lista-atendimentos-ativos");
  if (ativos.length === 0) {
    caixaAtivos.innerHTML = `<p class="vazio">Nenhum atendimento em andamento.</p>`;
  } else {
    caixaAtivos.innerHTML = ativos
      .map((atendimento) => {
        const paciente = atendimento.patient || {};
        const medico = atendimento.doctor || {};
        return `
        <div class="card-medico">
          <div>
            <strong>Atendimento #${atendimento.id}</strong><br>
            <small>Paciente: #${paciente.id || atendimento.patient_id} ${paciente.name || ""}</small><br>
            <small>Médico: ${medico.name || ""} • Início: ${atendimento.started_at || "-"}</small>
          </div>
          <span class="badge badge-${paciente.priority || 1}">${paciente.priority_label || "Em curso"}</span>
          <div class="card-acoes">
            <button type="button" class="btn-concluir" onclick="executarAcao('/api/attendances/${atendimento.id}/finish/')">Concluir</button>
            <button type="button" class="btn-cancelar" onclick="executarAcao('/api/attendances/${atendimento.id}/cancel/')">Cancelar</button>
          </div>
        </div>
      `;
      })
      .join("");
  }

  const medicos = snapshot.doctors || [];
  const caixaMedicos = document.getElementById("lista-medicos");
  if (medicos.length === 0) {
    caixaMedicos.innerHTML = `<p class="vazio">Nenhum médico cadastrado.</p>`;
  } else {
    caixaMedicos.innerHTML = medicos
      .map(
        (medico) => `
      <div class="card-medico">
        <div>
          <strong>#${medico.id} ${medico.name}</strong><br>
          <small>${medico.registry_code} • Concluídos: <strong>${medico.completed_count}</strong></small>
        </div>
        <span class="${medico.status === "Disponível" ? "status-disponivel" : "status-ocupado"}">
          ${medico.status}
        </span>
      </div>
    `,
      )
      .join("");
  }

  const historico = snapshot.history || [];
  const caixaHistorico = document.getElementById("lista-historico");
  if (historico.length === 0) {
    caixaHistorico.innerHTML = `<li>Nenhum atendimento finalizado ainda.</li>`;
  } else {
    caixaHistorico.innerHTML = historico
      .map((item) => {
        const paciente = item.patient || {};
        const medico = item.doctor || {};
        return `<li>#${paciente.id || item.patient_id} ${paciente.name || ""} — ${item.status} (${medico.name || "Sem médico"})</li>`;
      })
      .join("");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const campoChegada = document.getElementById("paciente-chegada");
  const horaAtual = () => new Date().toTimeString().slice(0, 5);
  campoChegada.value = horaAtual();

  try {
    const estadoInicial = await enviarRequisicao("/api/state/");
    atualizarTela(estadoInicial.snapshot);
  } catch (erro) {
    mostrarAviso(erro.message, true);
  }

  document
    .getElementById("form-paciente")
    .addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const dados = {
        name: document.getElementById("paciente-nome").value.trim(),
        arrival_time: campoChegada.value,
        priority: Number(document.getElementById("paciente-prioridade").value),
      };
      await executarAcao("/api/patients/", dados);
      evento.target.reset();
      campoChegada.value = horaAtual();
    });

  document
    .getElementById("form-medico")
    .addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const dados = {
        name: document.getElementById("medico-nome").value.trim(),
        registry_code: document.getElementById("medico-crm").value.trim(),
      };
      await executarAcao("/api/doctors/", dados);
      evento.target.reset();
    });

  document
    .getElementById("btn-chamar-proximo")
    .addEventListener("click", () => {
      executarAcao("/api/attendances/call/");
    });

  document.getElementById("btn-validar").addEventListener("click", () => {
    executarAcao("/api/validate/", {}, "Estruturas validadas com sucesso!");
  });

  document
    .getElementById("btn-buscar-paciente-id")
    .addEventListener("click", async () => {
      const id = document.getElementById("busca-paciente-id").value.trim();
      const resultado = document.getElementById("resultado-paciente-id");
      if (!id) return;

      try {
        const dados = await enviarRequisicao(`/api/patients/${id}/`);
        const p = dados.patient;
        resultado.innerHTML = `<strong>#${p.id} ${p.name}</strong> — ${p.priority_label} • Chegada: ${p.arrival_time} • Status: <strong>${p.status}</strong>`;
      } catch (erro) {
        resultado.textContent = erro.message;
      }
    });

  document
    .getElementById("btn-buscar-chegada")
    .addEventListener("click", async () => {
      const hora = document.getElementById("busca-chegada-hora").value;
      const id = document.getElementById("busca-chegada-id").value.trim();
      const resultado = document.getElementById("resultado-chegada");
      if (!hora || !id) return;

      try {
        const url = `/api/patients/search-arrival/?arrival_time=${encodeURIComponent(hora)}&patient_id=${encodeURIComponent(id)}`;
        const dados = await enviarRequisicao(url);
        const p = dados.patient;
        resultado.innerHTML = `<strong>#${p.id} ${p.name}</strong> — ${p.priority_label} • Chegada: ${p.arrival_time} • Status: <strong>${p.status}</strong>`;
      } catch (erro) {
        resultado.textContent = erro.message;
      }
    });

  document
    .getElementById("btn-buscar-medico-id")
    .addEventListener("click", async () => {
      const id = document.getElementById("busca-medico-id").value.trim();
      const resultado = document.getElementById("resultado-medico-id");
      if (!id) return;

      try {
        const dados = await enviarRequisicao(`/api/doctors/${id}/`);
        const m = dados.doctor;
        resultado.innerHTML = `<strong>#${m.id} ${m.name}</strong> (${m.registry_code}) — ${m.status} • Concluídos: <strong>${m.completed_count}</strong>`;
      } catch (erro) {
        resultado.textContent = erro.message;
      }
    });
});

document.addEventListener("DOMContentLoaded", async () => {
  const campoChegada = document.getElementById("paciente-chegada");
  const horaAtual = () => new Date().toTimeString().slice(0, 5);
  campoChegada.value = horaAtual();

  try {
    const estadoInicial = await enviarRequisicao("/api/state/");
    atualizarTela(estadoInicial.snapshot);
  } catch (erro) {
    mostrarAviso(erro.message, true);
  }

  document
    .getElementById("form-paciente")
    .addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const dados = {
        name: document.getElementById("paciente-nome").value.trim(),
        arrival_time: campoChegada.value,
        priority: Number(document.getElementById("paciente-prioridade").value),
      };
      await executarAcao("/api/patients/", dados);
      evento.target.reset();
      campoChegada.value = horaAtual();
    });

  document
    .getElementById("form-medico")
    .addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const dados = {
        name: document.getElementById("medico-nome").value.trim(),
        registry_code: document.getElementById("medico-crm").value.trim(),
      };
      await executarAcao("/api/doctors/", dados);
      evento.target.reset();
    });

  document
    .getElementById("btn-chamar-proximo")
    .addEventListener("click", () => {
      executarAcao("/api/attendances/call/");
    });

  document.getElementById("btn-validar").addEventListener("click", () => {
    executarAcao("/api/validate/", {}, "Estruturas validadas com sucesso!");
  });

  document
    .getElementById("btn-buscar-paciente-id")
    .addEventListener("click", async () => {
      const id = document.getElementById("busca-paciente-id").value.trim();
      const resultado = document.getElementById("resultado-paciente-id");
      if (!id) return;

      try {
        const dados = await enviarRequisicao(`/api/patients/${id}/`);
        const p = dados.patient;
        resultado.innerHTML = `<strong>#${p.id} ${p.name}</strong> — ${p.priority_label} • Chegada: ${p.arrival_time} • Status: <strong>${p.status}</strong>`;
      } catch (erro) {
        resultado.textContent = erro.message;
      }
    });

  document
    .getElementById("btn-buscar-chegada")
    .addEventListener("click", async () => {
      const hora = document.getElementById("busca-chegada-hora").value;
      const id = document.getElementById("busca-chegada-id").value.trim();
      const resultado = document.getElementById("resultado-chegada");
      if (!hora || !id) return;

      try {
        const url = `/api/patients/search-arrival/?arrival_time=${encodeURIComponent(hora)}&patient_id=${encodeURIComponent(id)}`;
        const dados = await enviarRequisicao(url);
        const p = dados.patient;
        resultado.innerHTML = `<strong>#${p.id} ${p.name}</strong> — ${p.priority_label} • Chegada: ${p.arrival_time} • Status: <strong>${p.status}</strong>`;
      } catch (erro) {
        resultado.textContent = erro.message;
      }
    });

  document
    .getElementById("btn-buscar-medico-id")
    .addEventListener("click", async () => {
      const id = document.getElementById("busca-medico-id").value.trim();
      const resultado = document.getElementById("resultado-medico-id");
      if (!id) return;

      try {
        const dados = await enviarRequisicao(`/api/doctors/${id}/`);
        const m = dados.doctor;
        resultado.innerHTML = `<strong>#${m.id} ${m.name}</strong> (${m.registry_code}) — ${m.status} • Concluídos: <strong>${m.completed_count}</strong>`;
      } catch (erro) {
        resultado.textContent = erro.message;
      }
    });
});
