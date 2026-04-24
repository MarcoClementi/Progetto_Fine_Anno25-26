/**
 * SmartPreventivo – Chatbot Frontend
 *
 * Gestisce tutta l'interazione con il chatbot tramite Fetch API (AJAX).
 * Comunicazione asincrona con il backend Flask (TPSIT – RF-10).
 *
 * Stato della chat mantenuto nell'oggetto `stato`:
 *   - session_token
 *   - categoria selezionata
 *   - domanda corrente
 *   - numero domanda / totale domande
 *   - lead_id (dopo salvataggio contatti)
 */

'use strict';

// ── Riferimenti DOM ────────────────────────────────────────────────────────
const fab          = document.getElementById('chat-fab');
const chatWindow   = document.getElementById('chat-window');
const btnChiudi    = document.getElementById('btn-chiudi-chat');
const areaMsg      = document.getElementById('chat-messaggi');
const areaOpzioni  = document.getElementById('chat-opzioni');
const progressBar  = document.getElementById('chat-progress-bar');

// ── Stato della chat ───────────────────────────────────────────────────────
const stato = {
  session_token:    null,
  categoria:        null,   // { id, nome, icona }
  domanda_corrente: null,   // { id, testo, tipo_input, opzioni, ordine }
  domanda_num:      0,
  domande_totali:   0,
  lead_id:          null,
  fase:             'init', // init | categorie | domande | contatti | stima | fine
};

// ── Apertura / chiusura finestra ───────────────────────────────────────────
fab.addEventListener('click', () => {
  if (!chatWindow.classList.contains('aperta')) {
    apriChat();
  }
});

btnChiudi.addEventListener('click', () => {
  chatWindow.classList.remove('aperta');
});

async function apriChat() {
  chatWindow.classList.add('aperta');
  if (stato.session_token) return; // già avviata in precedenza

  mostraTyping();
  try {
    const data = await chiamaAPI('/api/chat/start', {});
    rimuoviTyping();

    stato.session_token = data.session_token;
    stato.fase = 'categorie';

    aggiungiMessaggio('bot', data.messaggio);
    mostraCategorie(data.categorie);
  } catch (err) {
    rimuoviTyping();
    aggiungiMessaggio('bot', '⚠️ Errore di connessione. Riprova tra qualche istante.');
  }
}

// ── Mostra le categorie come pulsanti ──────────────────────────────────────
function mostraCategorie(categorie) {
  svuotaOpzioni();
  const grid = document.createElement('div');
  grid.className = 'chat-categorie';

  categorie.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'btn-categoria';
    btn.innerHTML = `<span class="cat-icon">${cat.icona}</span><span>${cat.nome}</span>`;
    btn.addEventListener('click', () => selezionaCategoria(cat));
    grid.appendChild(btn);
  });

  areaOpzioni.appendChild(grid);
}

// ── Selezione categoria ────────────────────────────────────────────────────
async function selezionaCategoria(cat) {
  aggiungiMessaggio('utente', `${cat.icona} ${cat.nome}`);
  svuotaOpzioni();
  mostraTyping();

  try {
    const data = await chiamaAPI('/api/chat/categoria', {
      session_token: stato.session_token,
      categoria_id: cat.id
    });
    rimuoviTyping();

    stato.categoria       = data.categoria;
    stato.domande_totali  = data.domande_totali;
    stato.domanda_num     = 1;
    stato.fase            = 'domande';

    aggiungiMessaggio('bot', data.messaggio);

    if (data.prima_domanda) {
      setTimeout(() => {
        aggiungiMessaggio('bot', data.prima_domanda.testo);
        stato.domanda_corrente = data.prima_domanda;
        aggiornaPrgresso();
        mostraOpzioniDomanda(data.prima_domanda);
      }, 400);
    }
  } catch (err) {
    rimuoviTyping();
    aggiungiMessaggio('bot', '⚠️ Errore. Riprova.');
  }
}

// ── Mostra le opzioni per una domanda ─────────────────────────────────────
function mostraOpzioniDomanda(domanda) {
  svuotaOpzioni();

  if (domanda.tipo_input === 'select' && domanda.opzioni.length > 0) {
    // Pulsanti per le opzioni predefinite
    domanda.opzioni.forEach(opzione => {
      const btn = document.createElement('button');
      btn.className = 'btn-opzione';
      btn.textContent = opzione;
      btn.addEventListener('click', () => inviaRisposta(opzione));
      areaOpzioni.appendChild(btn);
    });
  } else {
    // Input testuale libero
    const form = document.createElement('div');
    form.className = 'chat-form';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'chat-input';
    input.placeholder = 'Scrivi la tua risposta...';
    input.autocomplete = 'off';

    const btnSend = document.createElement('button');
    btnSend.className = 'btn-invia';
    btnSend.textContent = 'Invia →';

    const inviaLibero = () => {
      const val = input.value.trim();
      if (!val) return;
      inviaRisposta(val);
    };

    btnSend.addEventListener('click', inviaLibero);
    input.addEventListener('keypress', e => { if (e.key === 'Enter') inviaLibero(); });

    form.appendChild(input);
    form.appendChild(btnSend);
    areaOpzioni.appendChild(form);
    setTimeout(() => input.focus(), 100);
  }
}

// ── Invia risposta a una domanda ───────────────────────────────────────────
async function inviaRisposta(valore) {
  aggiungiMessaggio('utente', valore);
  svuotaOpzioni();
  mostraTyping();

  try {
    const data = await chiamaAPI('/api/chat/risposta', {
      session_token: stato.session_token,
      domanda_id: stato.domanda_corrente.id,
      valore: valore
    });
    rimuoviTyping();

    if (data.completato) {
      // Tutte le domande completate → form contatti
      stato.fase = 'contatti';
      stato.domanda_num = stato.domande_totali;
      aggiornaPrgresso();
      aggiungiMessaggio('bot', data.messaggio);
      setTimeout(mostraFormContatti, 400);
    } else {
      // Prossima domanda
      stato.domanda_num++;
      stato.domanda_corrente = data.prossima_domanda;
      aggiornaPrgresso();
      aggiungiMessaggio('bot', data.prossima_domanda.testo);
      setTimeout(() => mostraOpzioniDomanda(data.prossima_domanda), 200);
    }
  } catch (err) {
    rimuoviTyping();
    aggiungiMessaggio('bot', '⚠️ Errore. Riprova.');
  }
}

// ── Form raccolta dati di contatto ─────────────────────────────────────────
function mostraFormContatti() {
  svuotaOpzioni();

  const form = document.createElement('div');
  form.className = 'chat-form';

  const campi = [
    { name: 'nome',     type: 'text',  placeholder: 'Il tuo nome e cognome' },
    { name: 'telefono', type: 'tel',   placeholder: 'Telefono (es. 339 1234567)' },
    { name: 'email',    type: 'email', placeholder: 'La tua email' },
  ];

  const inputs = {};
  campi.forEach(campo => {
    const input = document.createElement('input');
    input.type = campo.type;
    input.className = 'chat-input';
    input.placeholder = campo.placeholder;
    input.name = campo.name;
    input.autocomplete = campo.name;
    inputs[campo.name] = input;
    form.appendChild(input);
  });

  const erroreDiv = document.createElement('div');
  erroreDiv.className = 'chat-errore hidden';

  const btnSend = document.createElement('button');
  btnSend.className = 'btn-invia';
  btnSend.textContent = '🔍 Calcola la mia stima';

  btnSend.addEventListener('click', async () => {
    btnSend.disabled = true;
    btnSend.textContent = 'Calcolo in corso...';
    erroreDiv.classList.add('hidden');

    const payload = {
      session_token: stato.session_token,
      categoria_id: stato.categoria.id,
      nome:     inputs['nome'].value.trim(),
      telefono: inputs['telefono'].value.trim(),
      email:    inputs['email'].value.trim(),
    };

    aggiungiMessaggio('utente', `📝 ${payload.nome} · ${payload.telefono} · ${payload.email}`);
    svuotaOpzioni();
    mostraTyping();

    try {
      const data = await chiamaAPI('/api/chat/contatti', payload);
      rimuoviTyping();

      stato.lead_id = data.lead_id;
      stato.fase = 'stima';

      aggiungiMessaggio('bot', `Ottimo ${payload.nome.split(' ')[0]}! Ho calcolato la tua stima. 🎉`);
      setTimeout(() => mostraStima(data), 500);
    } catch (err) {
      rimuoviTyping();
      btnSend.disabled = false;
      btnSend.textContent = '🔍 Calcola la mia stima';
      // Mostra eventuali errori di validazione
      const msg = err.errori ? err.errori.join('\n') : '⚠️ Errore. Controlla i dati inseriti.';
      erroreDiv.textContent = msg;
      erroreDiv.classList.remove('hidden');
      areaOpzioni.appendChild(form);
      areaOpzioni.appendChild(erroreDiv);
    }
  });

  form.appendChild(erroreDiv);
  form.appendChild(btnSend);
  areaOpzioni.appendChild(form);
}

// ── Mostra la stima finale ─────────────────────────────────────────────────
function mostraStima(data) {
  svuotaOpzioni();

  const card = document.createElement('div');
  card.className = 'stima-card';

  const stimaMin = Math.round(data.stima_min).toLocaleString('it-IT');
  const stimaMax = Math.round(data.stima_max).toLocaleString('it-IT');

  card.innerHTML = `
    <div class="stima-label">${stato.categoria.icona} ${stato.categoria.nome}</div>
    <div class="stima-range">€ ${stimaMin} – € ${stimaMax}</div>
    <div class="stima-nota">Stima indicativa. Riceverai un'email con i dettagli.</div>
    <button class="btn-sopralluogo" id="btn-sopralluogo">
      🏗️ Richiedi sopralluogo gratuito
    </button>
  `;

  areaOpzioni.appendChild(card);

  document.getElementById('btn-sopralluogo').addEventListener('click', richiediSopralluogo);

  // Aggiorna progress bar al 100%
  if (progressBar) progressBar.style.width = '100%';
}

// ── <<extend>> Richiedi sopralluogo ───────────────────────────────────────
async function richiediSopralluogo() {
  const btn = document.getElementById('btn-sopralluogo');
  if (btn) { btn.disabled = true; btn.textContent = 'Invio richiesta...'; }

  try {
    const data = await chiamaAPI('/api/lead/sopralluogo', { lead_id: stato.lead_id });
    svuotaOpzioni();
    aggiungiMessaggio('bot', data.messaggio);
    aggiungiMessaggio('sistema', '✅ Sopralluogo richiesto — ti contatteremo presto!');
  } catch (err) {
    aggiungiMessaggio('bot', '⚠️ Errore nella richiesta. Contattaci direttamente.');
  }
}

// ── Helper: aggiungi messaggio alla chat ──────────────────────────────────
function aggiungiMessaggio(mittente, testo) {
  const div = document.createElement('div');
  div.className = `msg msg-${mittente}`;
  div.textContent = testo;
  areaMsg.appendChild(div);
  scorriInFondo();
}

// ── Helper: typing indicator ──────────────────────────────────────────────
function mostraTyping() {
  const div = document.createElement('div');
  div.className = 'msg msg-typing';
  div.id = 'msg-typing';
  div.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  areaMsg.appendChild(div);
  scorriInFondo();
}

function rimuoviTyping() {
  const el = document.getElementById('msg-typing');
  if (el) el.remove();
}

// ── Helper: svuota area opzioni ───────────────────────────────────────────
function svuotaOpzioni() {
  areaOpzioni.innerHTML = '';
}

// ── Helper: scorrimento messaggi ──────────────────────────────────────────
function scorriInFondo() {
  areaMsg.scrollTop = areaMsg.scrollHeight;
}

// ── Helper: aggiorna progress bar ─────────────────────────────────────────
function aggiornaPrgresso() {
  if (!progressBar || stato.domande_totali === 0) return;
  const perc = Math.min((stato.domanda_num / stato.domande_totali) * 100, 100);
  progressBar.style.width = perc + '%';
}

// ── Helper: chiamata API con Fetch ────────────────────────────────────────
async function chiamaAPI(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  const data = await response.json();

  if (!response.ok) {
    // Propaga errori strutturati (es. errori di validazione)
    throw data;
  }

  return data;
}
