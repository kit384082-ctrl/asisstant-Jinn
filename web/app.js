"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const create = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};
const i18n = window.GenieI18n;
const t = (key, variables) => i18n.t(key, variables);

const kindMeta = {
  timer: { labelKey: "timer", icon: "◷", color: "violet" },
  reminder: { labelKey: "reminder", icon: "♢", color: "amber" },
  event: { labelKey: "event", icon: "▦", color: "cyan" },
  note: { labelKey: "note", icon: "✎", color: "rose" },
};
const appIcons = {
  globe: "◎", folder: "▰", terminal: ">_", calculator: "±", edit: "✎",
  code: "⌘", send: "➤", message: "◌", app: "◫",
};
const viewTitles = {
  chat: ["personalAgent", "dialogWith"],
  planner: ["yourTime", "planner"],
  apps: ["quickAccess", "apps"],
  github: ["workspace", "GitHub"],
};
const languageTags = { ru: "ru-RU", en: "en-US", de: "de-DE", es: "es-ES", fr: "fr-FR" };
const defaultWakePhrases = {
  ru: ["джинн", "эй джинн", "джини"], en: ["genie", "hey genie"], de: ["dschinni", "hallo dschinni"],
  es: ["genio", "hola genio"], fr: ["génie", "salut génie"],
};
const defaultTtsVoices = {
  ru: "ru-RU-SvetlanaNeural", en: "en-US-JennyNeural", de: "de-DE-KatjaNeural",
  es: "es-ES-ElviraNeural", fr: "fr-FR-DeniseNeural",
};
const githubActionLabels = {
  check_notifications: { ru: "Проверь уведомления", en: "Check notifications", de: "Prüfe Benachrichtigungen", es: "Revisa las notificaciones", fr: "Vérifie les notifications" },
  check_issues: { ru: "Покажи открытые задачи", en: "Show open issues", de: "Zeige offene Issues", es: "Muestra los issues abiertos", fr: "Affiche les issues ouvertes" },
  check_prs: { ru: "Покажи pull request’ы", en: "Show pull requests", de: "Zeige Pull Requests", es: "Muestra los pull requests", fr: "Affiche les pull requests" },
  check_actions: { ru: "Проверь GitHub Actions", en: "Check GitHub Actions", de: "Prüfe GitHub Actions", es: "Revisa GitHub Actions", fr: "Vérifie GitHub Actions" },
  recent_commits: { ru: "Покажи последние коммиты", en: "Show recent commits", de: "Zeige die letzten Commits", es: "Muestra los últimos commits", fr: "Affiche les derniers commits" },
};
const quickCommands = {
  timer: { ru: "Поставь таймер на 10 минут", en: "Set a timer for 10 minutes", de: "Stelle einen Timer für 10 Minuten", es: "Pon un temporizador de 10 minutos", fr: "Lance un minuteur de 10 minutes" },
  reminder: { ru: "Напомни завтра в 09:00 проверить почту", en: "Remind me tomorrow at 09:00 to check email", de: "Erinnere mich morgen um 09:00, E-Mails zu prüfen", es: "Recuérdame mañana a las 09:00 revisar el correo", fr: "Rappelle-moi demain à 09:00 de vérifier mes e-mails" },
  app: { ru: "Открой калькулятор", en: "Open calculator", de: "Öffne den Taschenrechner", es: "Abre la calculadora", fr: "Ouvre la calculatrice" },
  help: { ru: "Что ты умеешь?", en: "What can you do?", de: "Was kannst du?", es: "¿Qué puedes hacer?", fr: "Que sais-tu faire ?" },
};

const elements = {
  messages: $("#messages"), input: $("#command-input"), form: $("#command-form"),
  send: $("#send-button"), mic: $("#mic-button"), transcript: $("#voice-transcript"),
  interim: $("#interim-text"), count: $("#character-count"), portrait: $("#agent-portrait"),
  itemDialog: $("#item-dialog"), itemForm: $("#item-form"), appDialog: $("#app-dialog"),
  appForm: $("#app-form"), settingsDialog: $("#settings-dialog"), agenda: $("#agenda-list"),
  miniAgenda: $("#mini-agenda"), apps: $("#apps-grid"), calendar: $("#calendar-grid"),
  calendarTitle: $("#calendar-title"), toastStack: $("#toast-stack"), speechToggle: $("#speech-toggle"),
  languageSelector: $("#language-selector"), wakeToggle: $("#wake-toggle"), wakeState: $("#wake-mode-state"),
};

const state = {
  busy: false, connected: false, settings: {}, lastStatus: null, items: [], apps: [], recognition: null,
  listening: false, recognitionMode: "idle", pendingRecognitionMode: null, wakeArmed: false,
  wakeEnabled: localStorageSafeGet("genie-wake-mode") === "1", recognitionRestart: 0,
  currentView: "chat", agendaFilter: "all",
  calendarDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  lastNotificationId: Number(localStorageSafeGet("genie-last-notification") || 0),
  notificationHistoryKnown: localStorageSafeGet("genie-notification-initialized") === "1",
};
let welcomeTemplate = $("#welcome").cloneNode(true);
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function localStorageSafeGet(key) {
  try { return localStorage.getItem(key); } catch (_) { return null; }
}
function localStorageSafeSet(key, value) {
  try { localStorage.setItem(key, value); } catch (_) { /* private mode */ }
}

const appearanceDefaults = { theme: "system", accent: "violet", density: "comfortable", motion: "system" };
function storedAppearance() {
  try {
    const parsed = JSON.parse(localStorageSafeGet("jinn-appearance") || "{}");
    return {
      theme: ["system", "dark", "light"].includes(parsed.theme) ? parsed.theme : appearanceDefaults.theme,
      accent: ["violet", "cyan", "amber"].includes(parsed.accent) ? parsed.accent : appearanceDefaults.accent,
      density: ["comfortable", "compact"].includes(parsed.density) ? parsed.density : appearanceDefaults.density,
      motion: ["system", "reduced"].includes(parsed.motion) ? parsed.motion : appearanceDefaults.motion,
    };
  } catch (_) { return { ...appearanceDefaults }; }
}
function applyAppearance(preferences = storedAppearance()) {
  const root = document.documentElement;
  const darkSystem = window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? true;
  root.dataset.theme = preferences.theme === "system" ? (darkSystem ? "dark" : "light") : preferences.theme;
  root.dataset.accent = preferences.accent; root.dataset.density = preferences.density;
  root.dataset.motion = preferences.motion === "reduced" ? "reduced" : "system";
}
function saveAppearance(preferences) {
  localStorageSafeSet("jinn-appearance", JSON.stringify(preferences)); applyAppearance(preferences);
}
applyAppearance();
window.matchMedia?.("(prefers-color-scheme: dark)").addEventListener?.("change", () => {
  if (storedAppearance().theme === "system") applyAppearance();
});

async function api(path, body, timeoutMs = 35000) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const options = { headers: { Accept: "application/json" }, signal: controller.signal };
  if (body !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  try {
    const response = await fetch(path, options);
    let data;
    try { data = await response.json(); }
    catch (_) { throw new Error(t("serverInvalid", { status: response.status })); }
    if (!response.ok || !data.ok) {
      const message = data.error || t("httpError", { status: response.status });
      const error = new Error(
        data.solution ? `${message}\n${t("solution")}: ${data.solution}` : message,
      );
      error.code = data.code || `HTTP_${response.status}`; error.solution = data.solution || "";
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error(t("serverTimeout"));
    throw error;
  } finally { window.clearTimeout(timer); }
}

function formatClock(value = new Date()) {
  return new Intl.DateTimeFormat(languageTags[i18n.locale], { hour: "2-digit", minute: "2-digit" }).format(value);
}
function formatDate(value, options = {}) {
  return new Intl.DateTimeFormat(languageTags[i18n.locale], options).format(value);
}
function localInputValue(value) {
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}
function parseDue(item) { return item.due_at ? new Date(item.due_at) : null; }
function kindLabel(kind) { return t(kindMeta[kind]?.labelKey || "application"); }

function showToast(message, type = "info", title = type === "error" ? t("error") : t("agent")) {
  const toast = create("article", `toast ${type}`);
  toast.append(create("span", "", type === "error" ? "!" : "✦"));
  const copy = create("div");
  copy.append(create("strong", "", title), create("small", "", message));
  const close = create("button", "", "×");
  close.type = "button"; close.setAttribute("aria-label", t("close"));
  close.addEventListener("click", () => toast.remove());
  toast.append(copy, close);
  elements.toastStack.append(toast);
  window.setTimeout(() => toast.remove(), type === "error" ? 9000 : 5200);
}

function setBusy(busy) {
  state.busy = busy;
  elements.send.disabled = busy;
  $("#connect-button").disabled = busy;
  $$('[data-action]').forEach((button) => { button.disabled = busy; });
  elements.portrait.classList.toggle("busy", busy);
  if (busy && state.recognitionMode === "wake" && state.listening) state.recognition.stop();
  if (!busy && state.wakeEnabled && !state.listening) scheduleRecognition("wake");
}

function showView(name) {
  if (!(name in viewTitles)) return;
  state.currentView = name;
  $$("[data-view]").forEach((view) => {
    const active = view.dataset.view === name;
    view.hidden = !active;
    view.classList.toggle("active", active);
  });
  $$("[data-view-target]").forEach((button) => button.classList.toggle("active", button.dataset.viewTarget === name));
  $("#view-eyebrow").textContent = t(viewTitles[name][0]);
  $("#view-title").textContent = viewTitles[name][1] === "GitHub" ? "GitHub" : t(viewTitles[name][1]);
  document.body.classList.remove("menu-open");
  history.replaceState(null, "", `#${name}`);
  if (name === "planner") refreshAgenda();
  if (name === "apps") refreshApps();
}

function addMessage(role, text, options = {}) {
  const welcome = $("#welcome", elements.messages);
  if (welcome) welcome.hidden = true;
  const message = create("article", `message ${role}${options.error ? " error" : ""}`);
  const avatar = create("div", "message-avatar", role === "user" ? t("youAvatar") : t("agentAvatar"));
  const content = create("div", "message-content");
  content.append(create("div", "message-bubble", text), create("div", "message-meta", `${role === "user" ? t("you") : t("agent")} · ${formatClock()}`));
  message.append(avatar, content);
  elements.messages.append(message);
  elements.messages.scrollTo({ top: elements.messages.scrollHeight, behavior: "smooth" });
  return message;
}
function addTyping() {
  $("#typing-message")?.remove();
  const message = create("article", "message assistant"); message.id = "typing-message";
  const bubble = create("div", "message-bubble typing");
  for (let index = 0; index < 3; index += 1) bubble.append(create("i"));
  message.append(create("div", "message-avatar", t("agentAvatar")), bubble);
  elements.messages.append(message);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}
function removeTyping() { $("#typing-message")?.remove(); }

function preferredVoice() {
  const locale = i18n.locale;
  return window.speechSynthesis.getVoices().find((voice) => voice.lang.toLowerCase().startsWith(locale));
}
function speak(text) {
  if (!elements.speechToggle.checked || !("speechSynthesis" in window)) return;
  if (state.recognitionMode === "wake" && state.listening) state.recognition.stop();
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = languageTags[i18n.locale]; utterance.rate = 1;
  const voice = preferredVoice(); if (voice) utterance.voice = voice;
  utterance.onstart = () => elements.portrait.classList.add("speaking");
  utterance.onend = () => { elements.portrait.classList.remove("speaking"); if (state.wakeEnabled && !state.busy) scheduleRecognition("wake"); };
  utterance.onerror = utterance.onend;
  window.speechSynthesis.speak(utterance);
}

async function executeCommand(text) {
  const command = text.trim();
  if (!command || state.busy) return;
  showView("chat"); addMessage("user", command);
  elements.input.value = ""; resizeInput(); setBusy(true); addTyping();
  try {
    const result = await api("/api/command", { text: command, language: i18n.locale });
    removeTyping(); addMessage("assistant", result.response); speak(result.response);
    if (["create_timer", "create_reminder", "create_event", "create_note", "complete_item", "delete_item"].includes(result.intent?.action)) await refreshAgenda();
    if (result.intent?.action === "open_app") await refreshApps();
    await refreshStatus();
  } catch (error) {
    removeTyping(); addMessage("assistant", error.message, { error: true }); showToast(error.message, "error");
  } finally { setBusy(false); }
}

async function executeGithubAction(button) {
  if (state.busy) return;
  const action = button.dataset.action;
  showView("chat"); addMessage("user", githubActionLabels[action]?.[i18n.locale] || button.dataset.label);
  setBusy(true); addTyping();
  try {
    const result = await api("/api/action", { action, language: i18n.locale });
    removeTyping(); addMessage("assistant", result.response); speak(result.response); await refreshStatus();
  } catch (error) {
    removeTyping(); addMessage("assistant", error.message, { error: true }); showToast(error.message, "error");
  } finally { setBusy(false); }
}

function resizeInput() {
  elements.input.style.height = "auto";
  elements.input.style.height = `${Math.min(elements.input.scrollHeight, 120)}px`;
  elements.count.textContent = `${elements.input.value.length} / 4000`;
}
function setCapability(selector, ready, readyLabel, missingLabel) {
  const element = $(selector);
  element.textContent = ready ? readyLabel : missingLabel;
  element.classList.toggle("on", ready); element.classList.toggle("off", !ready);
}
function applyStatus(data) {
  state.lastStatus = data;
  state.connected = Boolean(data.connected);
  state.settings = data.settings || state.settings;
  if (!i18n.hasSavedSelection() && state.settings.ui_language && state.settings.ui_language !== i18n.selection) {
    i18n.setLocale(state.settings.ui_language, { persist: false });
  }
  $("#profile-repo").textContent = state.settings.github_repo || t("localMode");
  $("#github-repo-title").textContent = state.settings.github_repo || t("repoNotSet");
  $("#connect-button span").textContent = state.connected ? t("reconnect") : t("connect");
  const deps = data.dependencies || {};
  const providerConfigured = Boolean(state.settings.providers?.[state.settings.ai_provider]?.configured);
  setCapability("#dep-github", Boolean(deps.pygithub), t("ready"), t("notInstalled"));
  setCapability("#dep-openai", Boolean(deps.ai && providerConfigured), t("ready"), t("local"));
  setCapability("#dep-voice", Boolean(SpeechRecognition), t("ready"), t("noBrowserVoice"));
  if (data.agent) updateSummary(data.agent);
  $("#system-title").textContent = data.last_error ? t("needsCheck") : t("systemReady");
  $("#system-subtitle").textContent = data.last_error || (data.agent?.scheduler_running ? t("plannerRunning") : t("localMode"));
  updateWakeUI();
}
async function refreshStatus() {
  try { applyStatus(await api("/api/status")); }
  catch (error) { $("#system-title").textContent = t("serverUnavailable"); $("#system-subtitle").textContent = error.message; }
}
function updateSummary(agent) {
  const counts = agent.counts || {};
  $("#count-timers").textContent = counts.timer || 0; $("#count-reminders").textContent = counts.reminder || 0;
  $("#count-events").textContent = counts.event || 0; $("#count-notes").textContent = counts.note || 0;
  $("#nav-agenda-count").textContent = Object.values(counts).reduce((sum, count) => sum + count, 0);
}

function itemTimeLabel(item) {
  const due = parseDue(item);
  if (!due) return t("noDate");
  if (item.kind === "timer") return countdownLabel(due, true);
  return formatDate(due, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
function countdownLabel(due, precise = false) {
  const difference = due.getTime() - Date.now();
  if (difference <= 0) return t("timeArrived");
  const seconds = Math.ceil(difference / 1000); const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600); const minutes = Math.floor((seconds % 3600) / 60); const rest = seconds % 60;
  if (days) return `${days} ${t("dayShort")} ${hours} ${t("hourShort")}`;
  if (hours) return `${hours} ${t("hourShort")} ${minutes} ${t("minuteShort")}`;
  if (precise || minutes < 2) return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
  return `${minutes} ${t("minuteShort")}`;
}
function filteredItems() {
  if (state.agendaFilter === "all") return state.items;
  const allowed = state.agendaFilter.split(",");
  return state.items.filter((item) => allowed.includes(item.kind));
}
function makeAgendaItem(item) {
  const meta = kindMeta[item.kind];
  const article = create("article", `agenda-item${item.due_at && new Date(item.due_at) <= new Date() ? " due" : ""}`);
  article.dataset.itemId = item.id;
  const icon = create("span", `agenda-kind ${meta.color}`, meta.icon);
  const copy = create("span", "agenda-copy");
  copy.append(create("strong", "", item.title), create("small", "", item.details || kindLabel(item.kind)));
  const controls = create("span", "item-menu");
  if (item.due_at) {
    const time = create("time", "countdown", itemTimeLabel(item)); time.dataset.due = item.due_at; time.dataset.kind = item.kind; controls.append(time);
  }
  const complete = create("button", "", "✓"); complete.type = "button"; complete.title = t("completed"); complete.dataset.completeItem = item.id;
  const remove = create("button", "", "×"); remove.type = "button"; remove.title = t("delete"); remove.dataset.deleteItem = item.id;
  controls.append(complete, remove); article.append(icon, copy, controls); return article;
}
function renderAgenda() {
  elements.agenda.replaceChildren(); const items = filteredItems();
  if (!items.length) {
    const empty = create("div", "agenda-empty"); const copy = create("div");
    copy.append(create("span", "", "✦"), create("strong", "", t("emptyAgenda")), create("small", "", t("emptyAgendaHint"))); empty.append(copy); elements.agenda.append(empty);
  } else items.forEach((item) => elements.agenda.append(makeAgendaItem(item)));
  renderMiniAgenda(); renderCalendar();
}
function renderMiniAgenda() {
  elements.miniAgenda.replaceChildren(); const upcoming = state.items.filter((item) => item.due_at).slice(0, 5);
  if (!upcoming.length) { elements.miniAgenda.append(create("div", "mini-empty", t("noPlans"))); return; }
  upcoming.forEach((item) => {
    const meta = kindMeta[item.kind]; const row = create("div", "mini-item"); row.append(create("span", meta.color, meta.icon));
    const copy = create("div"); copy.append(create("strong", "", item.title), create("small", "", itemTimeLabel(item))); row.append(copy); elements.miniAgenda.append(row);
  });
}
function renderNextItem() {
  const item = state.items.find((entry) => entry.due_at); const copy = $("span:last-child", $("#next-item")); copy.replaceChildren();
  if (!item) copy.append(create("small", "", t("nextTask")), create("strong", "", t("freePlan")), create("em", "", t("rest")));
  else copy.append(create("small", "", kindLabel(item.kind)), create("strong", "", item.title), create("em", "", itemTimeLabel(item)));
}
async function refreshAgenda() {
  try {
    const data = await api("/api/agenda"); state.items = data.items || []; updateSummary(data.agent || {}); renderAgenda(); renderNextItem();
  } catch (error) { showToast(error.message, "error"); }
}
async function mutateItem(path, id) {
  try { await api(path, { id: Number(id) }); await refreshAgenda(); showToast(path.endsWith("complete") ? t("markedDone") : t("itemDeleted")); }
  catch (error) { showToast(error.message, "error"); }
}

function renderCalendar() {
  const year = state.calendarDate.getFullYear(); const month = state.calendarDate.getMonth();
  elements.calendarTitle.textContent = formatDate(state.calendarDate, { month: "long", year: "numeric" });
  const first = new Date(year, month, 1); const startOffset = (first.getDay() + 6) % 7; const start = new Date(year, month, 1 - startOffset);
  const todayKey = dateKey(new Date());
  const itemDates = new Set(state.items.filter((item) => item.due_at).map((item) => dateKey(new Date(item.due_at))));
  elements.calendar.replaceChildren();
  for (let index = 0; index < 42; index += 1) {
    const day = new Date(start); day.setDate(start.getDate() + index); const button = create("button", "calendar-day", String(day.getDate())); button.type = "button";
    button.classList.toggle("outside", day.getMonth() !== month); button.classList.toggle("today", dateKey(day) === todayKey);
    button.classList.toggle("has-items", itemDates.has(dateKey(day))); button.dataset.calendarDate = dateKey(day);
    button.title = formatDate(day, { dateStyle: "long" }); elements.calendar.append(button);
  }
}
function dateKey(value) { return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`; }

function selectItemKind(kind, prefillDate) {
  const titleInput = $("#item-title"); $("#item-kind").value = kind;
  $("#item-dialog-title").textContent = t("createLabel", { item: kindLabel(kind).toLocaleLowerCase(languageTags[i18n.locale]) });
  $("#item-title-label").textContent = kind === "timer" ? t("nameOptional") : t("name");
  titleInput.required = kind !== "timer";
  titleInput.placeholder = t({ timer: "createExample", reminder: "whatRemind", event: "eventName", note: "noteText" }[kind]);
  $("#duration-fields").hidden = kind !== "timer"; $("#due-field").hidden = !["reminder", "event"].includes(kind);
  $("#details-field").hidden = !["reminder", "event", "note"].includes(kind);
  $$("[data-kind]", elements.itemDialog).forEach((button) => button.classList.toggle("active", button.dataset.kind === kind));
  if (["reminder", "event"].includes(kind)) {
    const due = prefillDate ? new Date(`${prefillDate}T09:00:00`) : new Date(Date.now() + 3600000); due.setSeconds(0, 0); $("#item-due").value = localInputValue(due);
  }
}
function updateDurationLimit() {
  const duration = $("#item-duration"); const maximums = { 1: 2678400, 60: 44640, 3600: 744, 86400: 31 };
  duration.max = String(maximums[$("#item-duration-unit").value]); if (Number(duration.value) > Number(duration.max)) duration.value = duration.max;
}
function openItemDialog(kind = "timer", prefillDate = null) {
  elements.itemForm.reset(); $("#item-duration").value = "10"; $("#item-duration-unit").value = "60";
  updateDurationLimit(); selectItemKind(kind, prefillDate); elements.itemDialog.showModal(); window.setTimeout(() => $("#item-title").focus(), 80);
}
async function saveItem(event) {
  event.preventDefault(); const kind = $("#item-kind").value; const title = $("#item-title").value.trim(); const details = $("#item-details").value.trim();
  const button = $("#save-item"); button.disabled = true; button.textContent = t("creating");
  try {
    let path; let payload;
    if (kind === "timer") { path = "/api/timers"; payload = { label: title || t("timer"), duration_seconds: Number($("#item-duration").value) * Number($("#item-duration-unit").value) }; }
    else if (kind === "note") { path = "/api/notes"; payload = { title, details }; }
    else {
      const dueValue = $("#item-due").value; if (!dueValue) throw new Error(t("dueRequired"));
      path = kind === "event" ? "/api/events" : "/api/reminders"; payload = { title, details, due_at: new Date(dueValue).toISOString() };
    }
    await api(path, payload); elements.itemDialog.close(); await refreshAgenda(); showToast(t("created", { item: kindLabel(kind) }));
  } catch (error) { showToast(error.message, "error"); }
  finally { button.disabled = false; button.textContent = t("create"); }
}

function renderApps() {
  elements.apps.replaceChildren();
  state.apps.forEach((app) => {
    const card = create("article", `app-card tilt-card ${app.accent || "violet"}${app.available ? "" : " unavailable"}`);
    card.append(create("span", "app-icon", appIcons[app.icon] || "◫"), create("strong", "", app.name), create("small", "", app.available ? t(app.builtin ? "systemApp" : "addedByYou") : t("notFound")));
    const footer = create("footer"); const launch = create("button", "launch-app", app.available ? t("open") : t("unavailable"));
    launch.type = "button"; launch.disabled = !app.available; launch.dataset.launchApp = app.alias; footer.append(launch);
    if (!app.builtin) { const remove = create("button", "delete-app", "×"); remove.type = "button"; remove.title = t("delete"); remove.dataset.deleteApp = app.id; footer.append(remove); }
    card.append(footer); elements.apps.append(card);
  });
}
async function refreshApps() {
  try { const data = await api("/api/apps"); state.apps = data.apps || []; renderApps(); }
  catch (error) { showToast(error.message, "error"); }
}
async function launchApp(alias) {
  try { const result = await api("/api/apps/launch", { alias }); showToast(t("opening", { name: result.launched }), "info", t("application")); }
  catch (error) { showToast(error.message, "error"); }
}
async function saveApp(event) {
  event.preventDefault(); const button = $("#save-app"); button.disabled = true;
  try {
    const data = await api("/api/apps/register", { name: $("#app-name").value, executable: $("#app-path").value });
    state.apps = data.apps || []; renderApps(); elements.appDialog.close(); elements.appForm.reset(); showToast(t("appAdded"));
  } catch (error) { showToast(error.message, "error"); } finally { button.disabled = false; }
}
async function deleteApp(id) {
  try { const data = await api("/api/apps/delete", { id: Number(id) }); state.apps = data.apps || []; renderApps(); showToast(t("appRemoved")); }
  catch (error) { showToast(error.message, "error"); }
}

function secretState(id, configured) { $(id).textContent = t(configured ? "saved" : "missing"); }
function populateSettings() {
  const settings = state.settings; const providers = settings.providers || {};
  $("#setting-ui-language").value = i18n.hasSavedSelection() ? i18n.selection : (settings.ui_language || i18n.selection);
  $("#setting-repo").value = settings.github_repo || ""; $("#setting-ai-provider").value = settings.ai_provider || "openai";
  $("#setting-openai-model").value = providers.openai?.model || "gpt-4o-mini";
  $("#setting-openai-small-model").value = providers.openai?.small_model || "gpt-4o-mini";
  $("#setting-openai-base-url").value = settings.openai_base_url || providers.openai?.base_url || "https://api.openai.com/v1";
  $("#setting-gemini-model").value = providers.gemini?.model || "gemini-2.0-flash";
  $("#setting-gemini-small-model").value = providers.gemini?.small_model || "gemini-2.0-flash-lite";
  $("#setting-gemini-base-url").value = settings.gemini_base_url || providers.gemini?.base_url || "https://generativelanguage.googleapis.com/v1beta";
  $("#setting-anthropic-model").value = providers.anthropic?.model || "claude-3-5-haiku-latest";
  $("#setting-anthropic-small-model").value = providers.anthropic?.small_model || "claude-3-5-haiku-latest";
  $("#setting-anthropic-base-url").value = settings.anthropic_base_url || providers.anthropic?.base_url || "https://api.anthropic.com/v1";
  $("#setting-groq-model").value = providers.groq?.model || "llama-3.3-70b-versatile";
  $("#setting-groq-small-model").value = providers.groq?.small_model || "llama-3.1-8b-instant";
  $("#setting-groq-base-url").value = settings.groq_base_url || providers.groq?.base_url || "https://api.groq.com/openai/v1";
  $("#setting-ollama-model").value = providers.local?.model || "jinn";
  $("#setting-ollama-small-model").value = providers.local?.small_model || "jinn";
  $("#setting-ollama-base-url").value = settings.ollama_base_url || providers.local?.base_url || "http://127.0.0.1:11434/v1";
  $("#setting-custom-model").value = providers.custom?.model || "";
  $("#setting-custom-small-model").value = providers.custom?.small_model || "";
  $("#setting-custom-base-url").value = settings.custom_base_url || providers.custom?.base_url || "";
  $("#setting-small-model-mode").checked = Boolean(settings.ai_small_model_mode);
  $("#setting-ai-timeout").value = settings.ai_request_timeout ?? 30;
  $("#setting-ai-temperature").value = settings.ai_temperature ?? .35;
  $("#setting-ai-top-p").value = settings.ai_top_p ?? .9;
  $("#setting-ai-max-tokens").value = settings.ai_max_tokens ?? 1200;
  $("#setting-ai-frequency-penalty").value = settings.ai_frequency_penalty ?? 0;
  $("#setting-web-search").checked = Boolean(settings.web_search_enabled);
  $("#setting-search-results").value = settings.web_search_max_results ?? 5;
  const appearance = storedAppearance();
  $("#setting-theme").value = appearance.theme; $("#setting-accent").value = appearance.accent;
  $("#setting-density").value = appearance.density; $("#setting-motion").value = appearance.motion;
  $("#setting-voice-language").value = settings.voice_language || languageTags[i18n.locale];
  $("#setting-wake-words").value = settings.wake_words || defaultWakePhrases[i18n.locale].join(", ");
  $("#setting-vosk").value = settings.vosk_model_path || "model"; $("#setting-tts").value = settings.tts_voice || "";
  ["github-token", "openai-key", "google-key", "anthropic-key", "groq-key", "custom-key"].forEach((suffix) => { $(`#setting-${suffix}`).value = ""; });
  secretState("#github-token-state", settings.has_github_token); secretState("#openai-key-state", providers.openai?.configured);
  secretState("#gemini-key-state", providers.gemini?.configured); secretState("#anthropic-key-state", providers.anthropic?.configured);
  secretState("#groq-key-state", providers.groq?.configured); secretState("#custom-key-state", providers.custom?.configured);
  $("#local-model-state").textContent = `· ${t("local")}`;
  updateProviderPanels();
}
function updateProviderPanels() {
  const active = $("#setting-ai-provider").value;
  $$('[data-provider-card]').forEach((card) => card.classList.toggle("active", card.dataset.providerCard === active));
}
function updateVoiceLanguageDefaults() {
  const locale = $("#setting-voice-language").value.split("-", 1)[0].toLowerCase();
  if (!(locale in defaultWakePhrases)) return;
  $("#setting-wake-words").value = defaultWakePhrases[locale].join(", ");
  const tts = $("#setting-tts");
  if (!tts.value || Object.values(defaultTtsVoices).includes(tts.value)) tts.value = defaultTtsVoices[locale];
}
function appearanceFromForm() {
  return {
    theme: $("#setting-theme").value, accent: $("#setting-accent").value,
    density: $("#setting-density").value, motion: $("#setting-motion").value,
  };
}
function openSettings() { populateSettings(); elements.settingsDialog.showModal(); }
async function saveSettings(event) {
  event.preventDefault(); const button = $("#save-settings"); button.disabled = true; button.textContent = t("saving");
  const payload = {
    ui_language: $("#setting-ui-language").value, github_repo: $("#setting-repo").value, github_token: $("#setting-github-token").value,
    ai_provider: $("#setting-ai-provider").value, openai_api_key: $("#setting-openai-key").value,
    openai_model: $("#setting-openai-model").value, openai_small_model: $("#setting-openai-small-model").value,
    openai_base_url: $("#setting-openai-base-url").value,
    google_api_key: $("#setting-google-key").value, gemini_model: $("#setting-gemini-model").value,
    gemini_small_model: $("#setting-gemini-small-model").value, gemini_base_url: $("#setting-gemini-base-url").value,
    anthropic_api_key: $("#setting-anthropic-key").value, anthropic_model: $("#setting-anthropic-model").value,
    anthropic_small_model: $("#setting-anthropic-small-model").value, anthropic_base_url: $("#setting-anthropic-base-url").value,
    groq_api_key: $("#setting-groq-key").value, groq_model: $("#setting-groq-model").value,
    groq_small_model: $("#setting-groq-small-model").value, groq_base_url: $("#setting-groq-base-url").value,
    ollama_model: $("#setting-ollama-model").value, ollama_small_model: $("#setting-ollama-small-model").value,
    ollama_base_url: $("#setting-ollama-base-url").value,
    custom_api_key: $("#setting-custom-key").value, custom_model: $("#setting-custom-model").value,
    custom_small_model: $("#setting-custom-small-model").value, custom_base_url: $("#setting-custom-base-url").value,
    ai_small_model_mode: String($("#setting-small-model-mode").checked),
    ai_request_timeout: $("#setting-ai-timeout").value, ai_temperature: $("#setting-ai-temperature").value,
    ai_top_p: $("#setting-ai-top-p").value, ai_max_tokens: $("#setting-ai-max-tokens").value,
    ai_frequency_penalty: $("#setting-ai-frequency-penalty").value,
    web_search_enabled: String($("#setting-web-search").checked), web_search_max_results: $("#setting-search-results").value,
    voice_language: $("#setting-voice-language").value, wake_words: $("#setting-wake-words").value,
    vosk_model_path: $("#setting-vosk").value, tts_voice: $("#setting-tts").value,
  };
  try {
    const result = await api("/api/settings", payload); applyStatus(result); i18n.setLocale(payload.ui_language);
    saveAppearance(appearanceFromForm());
    elements.settingsDialog.close(); showToast(t("settingsSaved")); restartRecognitionForLanguage();
  } catch (error) { showToast(error.message, "error"); }
  finally { button.disabled = false; button.textContent = t("save"); }
}
async function connectGithub() {
  if (!state.settings.github_repo || !state.settings.has_github_token) { openSettings(); showToast(t("configureGithub")); return; }
  if (state.busy) return; setBusy(true);
  try { applyStatus(await api("/api/connect", {})); showToast(t("githubConnected")); }
  catch (error) { showToast(error.message, "error"); await refreshStatus(); } finally { setBusy(false); }
}

function updateNotificationState() {
  const element = $("#notification-state");
  if (!("Notification" in window)) element.textContent = t("notifUnsupported");
  else if (Notification.permission === "granted") element.textContent = t("notifAllowed");
  else if (Notification.permission === "denied") element.textContent = t("notifBlocked");
  else element.textContent = t("enable");
}
async function requestNotifications() {
  if (!("Notification" in window)) { showToast(t("browserNotifUnsupported"), "error"); return; }
  try {
    const permission = await Notification.requestPermission(); updateNotificationState();
    showToast(t(permission === "granted" ? "notifEnabled" : "notifDenied"), permission === "granted" ? "info" : "error");
  } catch (_) { showToast(t("notifRequestFailed"), "error"); }
}
function notificationTitle(notification) {
  const keys = { timer: "timerFinished", reminder: "reminder", event: "eventStarting", note: "note" };
  return keys[notification.kind] ? t(keys[notification.kind]) : notification.title;
}
function notifyUser(notification) {
  const title = notificationTitle(notification);
  showToast(notification.body, "info", title);
  if ("Notification" in window && Notification.permission === "granted") {
    try {
      const systemNotice = new Notification(title, { body: notification.body, icon: "/icon.svg", tag: `genie-${notification.id}` });
      systemNotice.onclick = () => { window.focus(); showView("planner"); systemNotice.close(); };
    } catch (_) { /* in-page notification remains visible */ }
  }
  playChime();
}
function playChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext; if (!AudioContext) return;
    const context = new AudioContext(); const oscillator = context.createOscillator(); const gain = context.createGain();
    oscillator.frequency.setValueAtTime(660, context.currentTime); oscillator.frequency.exponentialRampToValueAtTime(880, context.currentTime + .18);
    gain.gain.setValueAtTime(.0001, context.currentTime); gain.gain.exponentialRampToValueAtTime(.12, context.currentTime + .02); gain.gain.exponentialRampToValueAtTime(.0001, context.currentTime + .3);
    oscillator.connect(gain); gain.connect(context.destination); oscillator.start(); oscillator.stop(context.currentTime + .31); oscillator.onended = () => context.close();
  } catch (_) { /* audio is optional */ }
}
async function pollNotifications() {
  try {
    const data = await api(`/api/notifications?after=${state.lastNotificationId}`); const notifications = data.notifications || []; const shouldDisplay = state.notificationHistoryKnown;
    notifications.forEach((notification) => { state.lastNotificationId = Math.max(state.lastNotificationId, notification.id); if (shouldDisplay) notifyUser(notification); });
    if (notifications.length) localStorageSafeSet("genie-last-notification", String(state.lastNotificationId));
    if (!state.notificationHistoryKnown) { state.notificationHistoryKnown = true; localStorageSafeSet("genie-notification-initialized", "1"); }
    if (notifications.length) await refreshAgenda();
  } catch (_) { /* background polling stays silent */ }
}

function wakePhrases() {
  const configuredLocale = String(state.settings.voice_language || "").split("-", 1)[0].toLowerCase();
  const configured = String(state.settings.wake_words || "").split(",").map((word) => word.trim().toLocaleLowerCase(languageTags[i18n.locale])).filter(Boolean);
  return configuredLocale === i18n.locale && configured.length ? configured : defaultWakePhrases[i18n.locale];
}
function normalizeSpeech(text) { return text.toLocaleLowerCase(languageTags[i18n.locale]).replace(/[^\p{L}\p{N}]+/gu, " ").trim(); }
function extractWakeCommand(text) {
  const padded = ` ${normalizeSpeech(text)} `;
  for (const phrase of wakePhrases()) {
    const marker = ` ${normalizeSpeech(phrase)} `;
    const index = padded.indexOf(marker);
    if (index !== -1) return padded.slice(index + marker.length).trim();
  }
  return null;
}
function updateWakeUI(message = "") {
  elements.wakeToggle.disabled = !SpeechRecognition;
  elements.wakeToggle.checked = state.wakeEnabled;
  elements.wakeToggle.setAttribute("aria-pressed", String(state.wakeEnabled));
  elements.wakeToggle.classList.toggle("active", state.wakeEnabled);
  const phrase = wakePhrases()[0] || t("agent");
  elements.wakeState.textContent = message || (state.wakeEnabled ? t("wakeListening", { phrase }) : t("microphoneOff"));
  document.body.classList.toggle("wake-listening", state.wakeEnabled && state.listening && state.recognitionMode === "wake");
}
function clearRecognitionUI() {
  state.listening = false; elements.mic.classList.remove("listening"); elements.portrait.classList.remove("listening");
  elements.transcript.hidden = true; document.body.classList.remove("voice-listening", "wake-listening"); updateWakeUI();
}
function scheduleRecognition(mode, delay = 350) {
  window.clearTimeout(state.recognitionRestart);
  state.recognitionRestart = window.setTimeout(() => beginRecognition(mode), delay);
}
function beginRecognition(mode) {
  if (!state.recognition || state.listening || state.busy || (mode === "wake" && (!state.wakeEnabled || window.speechSynthesis?.speaking))) return;
  state.recognitionMode = mode; state.recognition.continuous = mode === "wake"; state.recognition.lang = languageTags[i18n.locale];
  try { state.recognition.start(); } catch (_) { if (mode === "wake" && state.wakeEnabled) scheduleRecognition("wake", 900); }
}
function setupRecognition() {
  if (!SpeechRecognition) {
    elements.mic.disabled = true; elements.mic.title = t("recognitionUnsupported"); state.wakeEnabled = false; updateWakeUI(); return;
  }
  const recognition = new SpeechRecognition(); recognition.interimResults = true; recognition.maxAlternatives = 1;
  recognition.onstart = () => {
    state.listening = true; elements.mic.classList.toggle("listening", state.recognitionMode === "command");
    elements.portrait.classList.add("listening"); elements.transcript.hidden = false;
    document.body.classList.toggle("voice-listening", state.recognitionMode === "command"); updateWakeUI();
  };
  recognition.onresult = (event) => {
    let finalText = ""; let interimText = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const transcript = event.results[index][0].transcript;
      if (event.results[index].isFinal) finalText += transcript; else interimText += transcript;
    }
    elements.interim.textContent = interimText || finalText || t("listening");
    if (!finalText) return;
    if (state.recognitionMode === "command") {
      elements.input.value = `${elements.input.value} ${finalText}`.trim(); resizeInput(); elements.input.focus(); return;
    }
    if (state.wakeArmed) {
      state.wakeArmed = false; updateWakeUI(); recognition.stop(); executeCommand(finalText); return;
    }
    const inlineCommand = extractWakeCommand(finalText);
    if (inlineCommand === null) return;
    if (inlineCommand) { recognition.stop(); executeCommand(inlineCommand); }
    else { state.wakeArmed = true; elements.interim.textContent = t("wakeHeard"); updateWakeUI(t("wakeHeard")); }
  };
  recognition.onerror = (event) => {
    const errors = { "not-allowed": t("allowMicrophone"), "service-not-allowed": t("allowMicrophone"), "no-speech": t("noSpeech"), network: t("speechUnavailable") };
    const quiet = event.error === "aborted" || (state.recognitionMode === "wake" && event.error === "no-speech");
    if (!quiet) showToast(errors[event.error] || t("microphoneError", { error: event.error }), "error");
    if (["not-allowed", "service-not-allowed"].includes(event.error)) { state.wakeEnabled = false; localStorageSafeSet("genie-wake-mode", "0"); }
  };
  recognition.onend = () => {
    clearRecognitionUI(); const pending = state.pendingRecognitionMode; state.pendingRecognitionMode = null;
    if (pending) scheduleRecognition(pending, 120); else if (state.wakeEnabled && !state.busy && !window.speechSynthesis?.speaking) scheduleRecognition("wake");
  };
  state.recognition = recognition; updateWakeUI(); if (state.wakeEnabled) scheduleRecognition("wake", 600);
}
function toggleRecognition() {
  if (!state.recognition) return;
  window.speechSynthesis?.cancel();
  if (state.listening) {
    if (state.recognitionMode === "wake") state.pendingRecognitionMode = "command";
    state.recognition.stop();
  } else beginRecognition("command");
}
function toggleWakeMode() {
  if (!state.recognition) { showToast(t("recognitionUnsupported"), "error"); return; }
  state.wakeEnabled = !state.wakeEnabled; state.wakeArmed = false;
  localStorageSafeSet("genie-wake-mode", state.wakeEnabled ? "1" : "0"); updateWakeUI();
  if (state.wakeEnabled) {
    if (!state.listening) beginRecognition("wake"); showToast(t("wakeOn"));
  } else {
    window.clearTimeout(state.recognitionRestart); if (state.listening && state.recognitionMode === "wake") state.recognition.stop(); showToast(t("wakeOff"));
  }
}
function restartRecognitionForLanguage() {
  if (!state.recognition) return;
  if (state.listening) state.recognition.stop(); else if (state.wakeEnabled) scheduleRecognition("wake", 120);
}

function updateClock() {
  const now = new Date(); $("#big-clock").textContent = formatClock(now);
  $("#sidebar-clock").textContent = formatDate(now, { weekday: "short", hour: "2-digit", minute: "2-digit" });
  $("#current-date").textContent = formatDate(now, { day: "numeric", month: "long" });
  $$('[data-due]').forEach((element) => {
    const due = new Date(element.dataset.due);
    element.textContent = element.dataset.kind === "timer" ? countdownLabel(due, true) : itemTimeLabel({ due_at: element.dataset.due, kind: element.dataset.kind });
    element.closest(".agenda-item")?.classList.toggle("due", due <= now);
  });
  renderNextItem();
}

function setupCinematicEffects() {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)"); const field = $("#particle-field");
  const buildParticles = () => {
    field.replaceChildren(); if (reduced.matches) return;
    for (let index = 0; index < 32; index += 1) {
      const particle = create("i", "particle");
      particle.style.setProperty("--x", `${Math.random() * 100}%`); particle.style.setProperty("--y", `${Math.random() * 100}%`);
      particle.style.setProperty("--size", `${1 + Math.random() * 3}px`); particle.style.setProperty("--delay", `${-Math.random() * 16}s`);
      particle.style.setProperty("--duration", `${12 + Math.random() * 20}s`); field.append(particle);
    }
  };
  buildParticles(); reduced.addEventListener?.("change", buildParticles);
  let frame = 0;
  window.addEventListener("pointermove", (event) => {
    if (reduced.matches || event.pointerType === "touch") return; window.cancelAnimationFrame(frame);
    frame = window.requestAnimationFrame(() => {
      const x = event.clientX / innerWidth - .5; const y = event.clientY / innerHeight - .5;
      document.documentElement.style.setProperty("--pointer-x", x.toFixed(3)); document.documentElement.style.setProperty("--pointer-y", y.toFixed(3));
    });
  }, { passive: true });
  document.addEventListener("pointermove", (event) => {
    const card = event.target.closest(".tilt-card, .welcome, .next-item"); if (!card || reduced.matches || event.pointerType === "touch") return;
    const box = card.getBoundingClientRect(); const x = (event.clientX - box.left) / box.width - .5; const y = (event.clientY - box.top) / box.height - .5;
    card.style.setProperty("--tilt-x", `${(-y * 4).toFixed(2)}deg`); card.style.setProperty("--tilt-y", `${(x * 5).toFixed(2)}deg`);
  }, { passive: true });
  document.addEventListener("pointerout", (event) => {
    const card = event.target.closest(".tilt-card, .welcome, .next-item");
    if (card && !card.contains(event.relatedTarget)) { card.style.removeProperty("--tilt-x"); card.style.removeProperty("--tilt-y"); }
  });
}

function relocalize() {
  showView(state.currentView); renderAgenda(); renderNextItem(); renderApps(); updateNotificationState(); updateWakeUI(); updateClock();
  if (state.lastStatus) applyStatus(state.lastStatus);
  const welcome = $("#welcome");
  if (welcome) { i18n.translateSubtree(welcome); welcomeTemplate = welcome.cloneNode(true); }
  restartRecognitionForLanguage();
}

// Navigation and global actions
$$("[data-view-target]").forEach((button) => button.addEventListener("click", () => showView(button.dataset.viewTarget)));
$$("[data-navigate]").forEach((link) => link.addEventListener("click", (event) => { event.preventDefault(); showView(link.dataset.navigate); }));
$("#mobile-menu").addEventListener("click", () => document.body.classList.toggle("menu-open"));
$("#sidebar-backdrop").addEventListener("click", () => document.body.classList.remove("menu-open"));
$("#quick-create").addEventListener("click", () => openItemDialog("reminder"));
$$("[data-create-kind]").forEach((button) => button.addEventListener("click", () => openItemDialog(button.dataset.createKind)));
$$("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => document.getElementById(button.dataset.closeDialog).close()));
$$(".modal").forEach((dialog) => dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); }));

// Chat
elements.form.addEventListener("submit", (event) => { event.preventDefault(); executeCommand(elements.input.value); });
elements.input.addEventListener("input", resizeInput);
elements.input.addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); elements.form.requestSubmit(); } });
elements.mic.addEventListener("click", toggleRecognition);
elements.messages.addEventListener("click", (event) => {
  const button = event.target.closest("[data-command]"); if (!button) return;
  const sources = Object.entries(quickCommands); const index = $$('[data-command]', elements.messages).indexOf(button); executeCommand(sources[index]?.[1][i18n.locale] || button.dataset.command);
});
$("#clear-chat").addEventListener("click", () => {
  const welcome = welcomeTemplate.cloneNode(true); i18n.translateSubtree(welcome);
  elements.messages.replaceChildren(welcome); window.speechSynthesis?.cancel();
});

// Planner
elements.itemForm.addEventListener("submit", saveItem); $("#item-duration-unit").addEventListener("change", updateDurationLimit);
$$("[data-kind]", elements.itemDialog).forEach((button) => button.addEventListener("click", () => selectItemKind(button.dataset.kind)));
$("#agenda-filter").addEventListener("click", (event) => {
  const button = event.target.closest("[data-filter]"); if (!button) return; state.agendaFilter = button.dataset.filter;
  $$("button", event.currentTarget).forEach((item) => item.classList.toggle("active", item === button)); renderAgenda();
});
elements.agenda.addEventListener("click", (event) => {
  const complete = event.target.closest("[data-complete-item]"); const remove = event.target.closest("[data-delete-item]");
  if (complete) mutateItem("/api/items/complete", complete.dataset.completeItem); if (remove) mutateItem("/api/items/delete", remove.dataset.deleteItem);
});
$("#calendar-prev").addEventListener("click", () => { state.calendarDate.setMonth(state.calendarDate.getMonth() - 1); state.calendarDate = new Date(state.calendarDate); renderCalendar(); });
$("#calendar-next").addEventListener("click", () => { state.calendarDate.setMonth(state.calendarDate.getMonth() + 1); state.calendarDate = new Date(state.calendarDate); renderCalendar(); });
$("#calendar-today").addEventListener("click", () => { state.calendarDate = new Date(new Date().getFullYear(), new Date().getMonth(), 1); renderCalendar(); });
elements.calendar.addEventListener("click", (event) => { const button = event.target.closest("[data-calendar-date]"); if (button) openItemDialog("event", button.dataset.calendarDate); });

// Applications and GitHub
$("#add-app-button").addEventListener("click", () => elements.appDialog.showModal()); elements.appForm.addEventListener("submit", saveApp);
elements.apps.addEventListener("click", (event) => {
  const launch = event.target.closest("[data-launch-app]"); const remove = event.target.closest("[data-delete-app]");
  if (launch) launchApp(launch.dataset.launchApp); if (remove && window.confirm(t("confirmDeleteApp"))) deleteApp(remove.dataset.deleteApp);
});
$$("[data-action]").forEach((button) => button.addEventListener("click", () => executeGithubAction(button))); $("#connect-button").addEventListener("click", connectGithub);

// Settings, language, voice, and notification controls
$("#settings-button").addEventListener("click", openSettings); $("#settings-form").addEventListener("submit", saveSettings);
$("#setting-ai-provider").addEventListener("change", updateProviderPanels);
["theme", "accent", "density", "motion"].forEach((name) => {
  $(`#setting-${name}`).addEventListener("change", () => saveAppearance(appearanceFromForm()));
});
$("#setting-voice-language").addEventListener("change", updateVoiceLanguageDefaults);
$("#notification-button").addEventListener("click", requestNotifications);
elements.languageSelector.addEventListener("change", () => i18n.setLocale(elements.languageSelector.value));
elements.wakeToggle.addEventListener("click", toggleWakeMode);
window.addEventListener("genie:languagechange", relocalize);
elements.speechToggle.addEventListener("change", () => {
  localStorageSafeSet("genie-speech", elements.speechToggle.checked ? "1" : "0"); if (!elements.speechToggle.checked) window.speechSynthesis?.cancel();
});
const savedSpeech = localStorageSafeGet("genie-speech"); if (savedSpeech !== null) elements.speechToggle.checked = savedSpeech === "1";

// Keyboard navigation
window.addEventListener("keydown", (event) => {
  if (event.altKey && ["1", "2", "3", "4"].includes(event.key)) { event.preventDefault(); showView(["chat", "planner", "apps", "github"][Number(event.key) - 1]); }
  if (event.key === "Escape") document.body.classList.remove("menu-open");
});

setupCinematicEffects(); setupRecognition(); resizeInput(); updateNotificationState();
showView(location.hash.slice(1) in viewTitles ? location.hash.slice(1) : "chat"); updateClock();
refreshStatus(); refreshAgenda(); refreshApps(); pollNotifications();
window.setInterval(updateClock, 1000); window.setInterval(pollNotifications, 3000); window.setInterval(refreshAgenda, 15000); window.setInterval(refreshStatus, 30000);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
