"use strict";

(() => {
  const languages = ["ru", "en", "de", "es", "fr"];
  const copy = {
    ru: {
      appTitle: "Джинн · Персональный агент", appDescription: "Джинн — локальный персональный ассистент",
      agent: "Джинн", brand: "ДЖИНН", personalAgent: "ПЕРСОНАЛЬНЫЙ АГЕНТ", agentActive: "Агент активен", yourTime: "ВАШЕ ВРЕМЯ", quickAccess: "БЫСТРЫЙ ДОСТУП", workspace: "РАБОЧЕЕ ПРОСТРАНСТВО", close: "Закрыть", dueRequired: "Укажите дату и время.",
      dialog: "Диалог", planner: "Планировщик", apps: "Приложения", quickCreate: "БЫСТРОЕ СОЗДАНИЕ",
      timer: "Таймер", reminder: "Напоминание", event: "Событие", note: "Заметка",
      timers: "Таймеры", reminders: "Напоминания", events: "События", notes: "Заметки",
      notifications: "Уведомления", enable: "включить", settings: "Настройки", localMode: "Локальный режим",
      dialogWith: "Диалог с Джинном", localSecure: "Локально и безопасно", readyCommands: "готов к командам",
      clear: "Очистить", yourAgent: "ВАШ ПЕРСОНАЛЬНЫЙ АГЕНТ", greetingDay: "Добрый день.",
      whatNext: "Чем займёмся?", welcomeDescription: "Говорите естественно — я пойму команду, создам план или просто поддержу разговор.",
      timer10: "Таймер на 10 минут", timeControl: "Контроль времени", remindTomorrow: "Напомнить завтра",
      forgetNothing: "Ничего не забыть", openApp: "Открыть приложение", quickLaunch: "Быстрый запуск",
      genieAbilities: "Возможности Джинна", meet: "Познакомиться", listening: "Слушаю…",
      sendHint: "отправить ·", newLine: "новая строка", schedule: "РАСПИСАНИЕ", upcoming: "Ближайшие дела",
      all: "Все", plans: "Планы", calendar: "КАЛЕНДАРЬ", today: "Сегодня",
      mon: "Пн", tue: "Вт", wed: "Ср", thu: "Чт", fri: "Пт", sat: "Сб", sun: "Вс",
      exportCalendar: "Экспортировать календарь .ics", localLaunch: "ЛОКАЛЬНЫЙ ЗАПУСК",
      appsDescription: "Открывайте голосом или одним нажатием. Команды выполняются без shell.",
      addApp: "Добавить приложение", onlyComputer: "Только на этом компьютере",
      remoteBlocked: "Из удалённого подключения запуск и настройка приложений заблокированы.",
      githubWorkspace: "GITHUB COPILOT ДЛЯ РЕПОЗИТОРИЯ", repoNotSet: "Репозиторий не настроен",
      githubDescription: "Проверяйте проект и добавляйте записи в файлы голосовыми командами. Все изменения строго направляются в",
      connect: "Подключиться", reconnect: "Переподключить", githubEvents: "Новые события GitHub",
      issues: "Задачи", openIssues: "Открытые issues", mergeRequests: "Запросы на слияние",
      lastWorkflow: "Последний workflow", commits: "Коммиты", lastChanges: "Последние изменения",
      now: "СЕЙЧАС", nextTask: "Ближайшее дело", freePlan: "План свободен", rest: "Можно немного отдохнуть",
      activity: "АКТИВНОСТЬ", myDay: "Мой день", systemReady: "Система готова",
      plannerRunning: "Планировщик работает", openConversation: "Свободный диалог", voice: "Голос",
      speakAnswers: "Озвучивать ответы", wakePhrase: "Фраза пробуждения", microphoneOff: "Микрофон выключен",
      newEntry: "НОВАЯ ЗАПИСЬ", create: "Создать", name: "Название", duration: "Длительность", unit: "Единица",
      minutes: "Минуты", seconds: "Секунды", hours: "Часы", days: "Дни", dateTime: "Дата и время",
      description: "Описание", cancel: "Отмена", secureLaunch: "БЕЗОПАСНЫЙ ЗАПУСК",
      appPathInfo: "Укажите абсолютный путь к исполняемому файлу. Аргументы и shell-команды не поддерживаются.",
      executable: "Исполняемый файл", add: "Добавить", configuration: "КОНФИГУРАЦИЯ", genieSettings: "Настройки Джинна",
      secretsLocal: "API-ключи сохраняются только в локальном", secretsSuffix: "и никогда не возвращаются браузеру.",
      interface: "Интерфейс", interfaceInfo: "Автовыбор языка браузера или постоянный ручной выбор.", language: "Язык",
      autoBrowser: "Авто — язык браузера", repositoryInfo: "Репозиторий и fine-grained token.", repository: "Репозиторий",
      aiProviders: "AI-провайдеры", providersInfo: "Выберите активный сервис. Можно безопасно сохранить отдельный ключ для каждого провайдера.",
      activeProvider: "Активный провайдер", customProvider: "Другой / собственный", model: "Модель",
      localModel: "Локальная модель 1.5B", localModelInfo: "Бесплатно и без облачного API-ключа. Требуется Ollama на этом компьютере.", ollamaUrl: "Локальный URL Ollama",
      backgroundVoice: "Фоновый голос", voiceInfo: "Выберите язык соответствующей модели Vosk, фразы пробуждения и голос TTS.",
      recognitionLanguage: "Язык распознавания", wakePhrases: "Фразы пробуждения", commaSeparated: "Через запятую",
      voskPath: "Путь к модели Vosk", ttsVoice: "Голос TTS", branchLock: "⌾ Запись GitHub только в", save: "Сохранить",
      auto: "Авто", uiLanguage: "Язык интерфейса", createExample: "Например, сделать перерыв", whatRemind: "Что напомнить?",
      eventName: "Название события", noteText: "Текст заметки", extraDetails: "Дополнительные детали…",
      leaveBlank: "Оставьте пустым, чтобы не менять", openMenu: "Открыть меню", clearDialog: "Очистить диалог",
      quickNote: "Быстрая заметка", commandPlaceholder: "Напишите или произнесите команду…", commandAria: "Команда для Джинна",
      voiceInput: "Голосовой ввод", send: "Отправить", createAction: "Создать", saved: "· сохранён", missing: "· не задан",
      you: "Вы", youAvatar: "ВЫ", agentAvatar: "ДЖ", error: "Ошибка", noDate: "Без даты", timeArrived: "время пришло",
      completed: "Выполнено", delete: "Удалить", emptyAgenda: "Здесь пока свободно",
      emptyAgendaHint: "Создайте таймер, напоминание или заметку", noPlans: "Пока нет запланированных дел",
      creating: "Создаю…", saving: "Сохраняю…", created: "{item} создан.", markedDone: "Отмечено как выполненное.",
      itemDeleted: "Запись удалена.", systemApp: "Системное приложение", addedByYou: "Добавлено вами", notFound: "Не найдено",
      open: "Открыть", unavailable: "Недоступно", application: "Приложение", opening: "Открываю «{name}».",
      appAdded: "Приложение добавлено.", appRemoved: "Приложение удалено из списка.", confirmDeleteApp: "Удалить приложение из списка Джинна?",
      settingsSaved: "Настройки сохранены.", githubConnected: "GitHub подключён.", configureGithub: "Укажите репозиторий и GitHub token.",
      notifUnsupported: "не поддерживаются", notifAllowed: "разрешены", notifBlocked: "заблокированы",
      browserNotifUnsupported: "Браузер не поддерживает системные уведомления.", notifEnabled: "Уведомления включены.",
      notifDenied: "Разрешение не выдано.", notifRequestFailed: "Не удалось запросить разрешение на уведомления.",
      recognitionUnsupported: "Распознавание речи не поддерживается", allowMicrophone: "Разрешите доступ к микрофону.",
      noSpeech: "Речь не распознана.", speechUnavailable: "Сервис речи недоступен.", microphoneError: "Ошибка микрофона: {error}",
      wakeListening: "Ожидаю «{phrase}»", wakeHeard: "Фраза услышана — говорите команду…", wakeOn: "Фоновое прослушивание включено.",
      wakeOff: "Фоновое прослушивание выключено.", ready: "готов", notInstalled: "не установлен", local: "локально",
      noBrowserVoice: "нет в браузере", needsCheck: "Нужна проверка", serverUnavailable: "Сервер недоступен",
      serverInvalid: "Сервер вернул некорректный ответ ({status}).", serverTimeout: "Сервер не ответил вовремя.", httpError: "Ошибка HTTP {status}",
      nameOptional: "Название (необязательно)", createLabel: "Создать: {item}", dayShort: "дн.", hourShort: "ч.", minuteShort: "мин.",
      sections: "Разделы", appNameExample: "Например, Figma", appPathExample: "C:\\Program Files\\App\\app.exe или /usr/bin/app",
      apiKey: "API-ключ", baseUrl: "Базовый URL", githubToken: "GitHub-токен", live: "ЭФИР",
      primaryModel: "Основная модель", economyModel: "Экономичная модель", localJinnModel: "Локальная модель Jinn 1.5B",
      localJinnInfo: "Бесплатно и без облачного API-ключа. Требуется Ollama и локальная модель jinn.", advancedAi: "Расширенная конфигурация AI",
      advancedAiInfo: "Экономичный маршрут, параметры генерации и ограниченный поиск. Поисковые фрагменты считаются недоверенными данными.", economyRoute: "Всегда использовать экономичную модель",
      timeoutSeconds: "Таймаут, секунд", temperature: "Температура", topP: "Top P", maxTokens: "Максимум токенов", frequencyPenalty: "Штраф частоты",
      searchResults: "Результатов поиска", webSearch: "Разрешить локальной Jinn искать в интернете", appearance: "Оформление", appearanceInfo: "Эти предпочтения хранятся только в вашем браузере.",
      theme: "Тема", systemTheme: "Как в системе", darkTheme: "Тёмная", lightTheme: "Светлая", accent: "Акцент", violet: "Фиолетовый", cyan: "Голубой", amber: "Янтарный",
      density: "Плотность", comfortable: "Комфортная", compact: "Компактная", animation: "Анимация", reduced: "Сокращённая", solution: "Что сделать",
      timerFinished: "Таймер завершён", eventStarting: "Событие начинается",
    },
    en: {
      appTitle: "Genie · Personal Agent", appDescription: "Genie — local personal assistant", agent: "Genie", brand: "GENIE", personalAgent: "PERSONAL AGENT", agentActive: "Agent active", yourTime: "YOUR TIME", quickAccess: "QUICK ACCESS", workspace: "WORKSPACE", close: "Close", dueRequired: "Enter a date and time.",
      dialog: "Chat", planner: "Planner", apps: "Applications", quickCreate: "QUICK CREATE", timer: "Timer", reminder: "Reminder", event: "Event", note: "Note",
      timers: "Timers", reminders: "Reminders", events: "Events", notes: "Notes", notifications: "Notifications", enable: "enable", settings: "Settings", localMode: "Local mode",
      dialogWith: "Chat with Genie", localSecure: "Local and secure", readyCommands: "ready for commands", clear: "Clear", yourAgent: "YOUR PERSONAL AGENT",
      greetingDay: "Good day.", whatNext: "What shall we do?", welcomeDescription: "Speak naturally — I’ll understand the command, build a plan or simply have a conversation.",
      timer10: "10-minute timer", timeControl: "Time control", remindTomorrow: "Remind me tomorrow", forgetNothing: "Forget nothing", openApp: "Open an application", quickLaunch: "Quick launch",
      genieAbilities: "What Genie can do", meet: "Get acquainted", listening: "Listening…", sendHint: "send ·", newLine: "new line", schedule: "SCHEDULE", upcoming: "Upcoming",
      all: "All", plans: "Plans", calendar: "CALENDAR", today: "Today", mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun",
      exportCalendar: "Export calendar .ics", localLaunch: "LOCAL LAUNCH", appsDescription: "Open by voice or with one click. Commands run without a shell.", addApp: "Add application",
      onlyComputer: "Only on this computer", remoteBlocked: "Application launching and setup are blocked from remote connections.", githubWorkspace: "GITHUB REPOSITORY COPILOT",
      repoNotSet: "Repository not configured", githubDescription: "Inspect the project and append to files with voice commands. All changes are strictly directed to", connect: "Connect", reconnect: "Reconnect",
      githubEvents: "New GitHub activity", issues: "Issues", openIssues: "Open issues", mergeRequests: "Merge requests", lastWorkflow: "Latest workflow", commits: "Commits", lastChanges: "Latest changes",
      now: "NOW", nextTask: "Next item", freePlan: "Your schedule is clear", rest: "Take a little break", activity: "ACTIVITY", myDay: "My day", systemReady: "System ready",
      plannerRunning: "Planner is running", openConversation: "Open conversation", voice: "Voice", speakAnswers: "Speak responses", wakePhrase: "Wake phrase", microphoneOff: "Microphone off",
      newEntry: "NEW ITEM", create: "Create", name: "Name", duration: "Duration", unit: "Unit", minutes: "Minutes", seconds: "Seconds", hours: "Hours", days: "Days",
      dateTime: "Date and time", description: "Description", cancel: "Cancel", secureLaunch: "SAFE LAUNCH", appPathInfo: "Enter an absolute executable path. Arguments and shell commands are not supported.",
      executable: "Executable", add: "Add", configuration: "CONFIGURATION", genieSettings: "Genie settings", secretsLocal: "API keys are saved only in the local", secretsSuffix: "and are never returned to the browser.",
      interface: "Interface", interfaceInfo: "Use the browser language automatically or keep a manual selection.", language: "Language", autoBrowser: "Auto — browser language",
      repositoryInfo: "Repository and fine-grained token.", repository: "Repository", aiProviders: "AI providers", providersInfo: "Choose the active service. You can safely save a separate key for every provider.",
      activeProvider: "Active provider", customProvider: "Other / custom", model: "Model", localModel: "Local 1.5B model", localModelInfo: "Free with no cloud API key. Ollama is required on this computer.", ollamaUrl: "Local Ollama URL", backgroundVoice: "Background voice", voiceInfo: "Choose the language of the matching Vosk model, wake phrases and TTS voice.",
      recognitionLanguage: "Recognition language", wakePhrases: "Wake phrases", commaSeparated: "Comma-separated", voskPath: "Vosk model path", ttsVoice: "TTS voice", branchLock: "⌾ GitHub writes only to", save: "Save",
      auto: "Auto", uiLanguage: "Interface language", createExample: "For example, take a break", whatRemind: "What should I remind you?", eventName: "Event name", noteText: "Note text",
      extraDetails: "Additional details…", leaveBlank: "Leave blank to keep unchanged", openMenu: "Open menu", clearDialog: "Clear conversation", quickNote: "Quick note",
      commandPlaceholder: "Type or say a command…", commandAria: "Command for Genie", voiceInput: "Voice input", send: "Send", createAction: "Create", saved: "· saved", missing: "· not set",
      you: "You", youAvatar: "YOU", agentAvatar: "GN", error: "Error", noDate: "No date", timeArrived: "due now", completed: "Complete", delete: "Delete",
      emptyAgenda: "Nothing here yet", emptyAgendaHint: "Create a timer, reminder or note", noPlans: "Nothing scheduled yet", creating: "Creating…", saving: "Saving…", created: "{item} created.",
      markedDone: "Marked as complete.", itemDeleted: "Item deleted.", systemApp: "System application", addedByYou: "Added by you", notFound: "Not found", open: "Open", unavailable: "Unavailable",
      application: "Application", opening: "Opening “{name}”.", appAdded: "Application added.", appRemoved: "Application removed from the list.", confirmDeleteApp: "Remove this application from Genie?",
      settingsSaved: "Settings saved.", githubConnected: "GitHub connected.", configureGithub: "Enter a repository and GitHub token.", notifUnsupported: "not supported", notifAllowed: "allowed",
      notifBlocked: "blocked", browserNotifUnsupported: "This browser does not support system notifications.", notifEnabled: "Notifications enabled.", notifDenied: "Permission was not granted.",
      notifRequestFailed: "Could not request notification permission.", recognitionUnsupported: "Speech recognition is not supported", allowMicrophone: "Allow microphone access.", noSpeech: "No speech recognized.",
      speechUnavailable: "Speech recognition service is unavailable.", microphoneError: "Microphone error: {error}", wakeListening: "Waiting for “{phrase}”", wakeHeard: "Wake phrase heard — say a command…",
      wakeOn: "Background listening enabled.", wakeOff: "Background listening disabled.", ready: "ready", notInstalled: "not installed", local: "local", noBrowserVoice: "not in browser", needsCheck: "Check required",
      serverUnavailable: "Server unavailable", serverInvalid: "The server returned an invalid response ({status}).", serverTimeout: "The server did not respond in time.", httpError: "HTTP error {status}",
      nameOptional: "Name (optional)", createLabel: "Create: {item}", dayShort: "d", hourShort: "h", minuteShort: "min",
      sections: "Sections", appNameExample: "For example, Figma", appPathExample: "C:\\Program Files\\App\\app.exe or /usr/bin/app",
      apiKey: "API key", baseUrl: "Base URL", githubToken: "GitHub token", live: "LIVE",
      primaryModel: "Primary model", economyModel: "Economy model", localJinnModel: "Local Jinn 1.5B model",
      localJinnInfo: "Free with no cloud API key. Ollama and the local jinn model are required.", advancedAi: "Advanced AI configuration",
      advancedAiInfo: "Economy routing, generation controls, and bounded search. Search snippets are treated as untrusted data.", economyRoute: "Always use the economy model",
      timeoutSeconds: "Timeout, seconds", temperature: "Temperature", topP: "Top P", maxTokens: "Maximum tokens", frequencyPenalty: "Frequency penalty",
      searchResults: "Search results", webSearch: "Allow local Jinn to search the internet", appearance: "Appearance", appearanceInfo: "These preferences are stored only in your browser.",
      theme: "Theme", systemTheme: "Follow system", darkTheme: "Dark", lightTheme: "Light", accent: "Accent", violet: "Violet", cyan: "Cyan", amber: "Amber",
      density: "Density", comfortable: "Comfortable", compact: "Compact", animation: "Motion", reduced: "Reduced", solution: "How to fix it",
      timerFinished: "Timer finished", eventStarting: "Event starting",
    },
    de: {
      appTitle: "Dschinni · Persönlicher Agent", appDescription: "Dschinni — lokaler persönlicher Assistent", agent: "Dschinni", brand: "DSCHINNI", personalAgent: "PERSÖNLICHER AGENT", agentActive: "Agent aktiv", yourTime: "DEINE ZEIT", quickAccess: "SCHNELLZUGRIFF", workspace: "ARBEITSBEREICH", close: "Schließen", dueRequired: "Datum und Uhrzeit eingeben.",
      dialog: "Dialog", planner: "Planer", apps: "Anwendungen", quickCreate: "SCHNELL ERSTELLEN", timer: "Timer", reminder: "Erinnerung", event: "Termin", note: "Notiz",
      timers: "Timer", reminders: "Erinnerungen", events: "Termine", notes: "Notizen", notifications: "Benachrichtigungen", enable: "aktivieren", settings: "Einstellungen", localMode: "Lokaler Modus",
      dialogWith: "Dialog mit Dschinni", localSecure: "Lokal und sicher", readyCommands: "bereit für Befehle", clear: "Leeren", yourAgent: "DEIN PERSÖNLICHER AGENT",
      greetingDay: "Guten Tag.", whatNext: "Was wollen wir tun?", welcomeDescription: "Sprich ganz natürlich — ich verstehe Befehle, erstelle Pläne oder unterhalte mich einfach.",
      timer10: "Timer für 10 Minuten", timeControl: "Zeit im Blick", remindTomorrow: "Morgen erinnern", forgetNothing: "Nichts vergessen", openApp: "Anwendung öffnen", quickLaunch: "Schnellstart",
      genieAbilities: "Dschinnis Fähigkeiten", meet: "Kennenlernen", listening: "Ich höre zu…", sendHint: "senden ·", newLine: "neue Zeile", schedule: "ZEITPLAN", upcoming: "Nächste Aufgaben",
      all: "Alle", plans: "Pläne", calendar: "KALENDER", today: "Heute", mon: "Mo", tue: "Di", wed: "Mi", thu: "Do", fri: "Fr", sat: "Sa", sun: "So",
      exportCalendar: "Kalender als .ics exportieren", localLaunch: "LOKALER START", appsDescription: "Per Sprache oder Klick öffnen. Befehle laufen ohne Shell.", addApp: "Anwendung hinzufügen",
      onlyComputer: "Nur auf diesem Computer", remoteBlocked: "Start und Einrichtung von Anwendungen sind aus Remote-Verbindungen gesperrt.", githubWorkspace: "GITHUB-COPILOT FÜR DAS REPOSITORY",
      repoNotSet: "Repository nicht eingerichtet", githubDescription: "Prüfe das Projekt und ergänze Dateien per Sprachbefehl. Alle Änderungen gehen strikt an", connect: "Verbinden", reconnect: "Neu verbinden",
      githubEvents: "Neue GitHub-Ereignisse", issues: "Issues", openIssues: "Offene Issues", mergeRequests: "Merge-Anfragen", lastWorkflow: "Letzter Workflow", commits: "Commits", lastChanges: "Letzte Änderungen",
      now: "JETZT", nextTask: "Nächste Aufgabe", freePlan: "Der Plan ist frei", rest: "Zeit für eine kleine Pause", activity: "AKTIVITÄT", myDay: "Mein Tag", systemReady: "System bereit",
      plannerRunning: "Planer läuft", openConversation: "Freier Dialog", voice: "Sprache", speakAnswers: "Antworten vorlesen", wakePhrase: "Aktivierungsphrase", microphoneOff: "Mikrofon aus",
      newEntry: "NEUER EINTRAG", create: "Erstellen", name: "Name", duration: "Dauer", unit: "Einheit", minutes: "Minuten", seconds: "Sekunden", hours: "Stunden", days: "Tage",
      dateTime: "Datum und Uhrzeit", description: "Beschreibung", cancel: "Abbrechen", secureLaunch: "SICHERER START", appPathInfo: "Gib einen absoluten Pfad zur ausführbaren Datei an. Argumente und Shell-Befehle werden nicht unterstützt.",
      executable: "Ausführbare Datei", add: "Hinzufügen", configuration: "KONFIGURATION", genieSettings: "Dschinni-Einstellungen", secretsLocal: "API-Schlüssel werden nur in der lokalen", secretsSuffix: "gespeichert und nie an den Browser zurückgegeben.",
      interface: "Oberfläche", interfaceInfo: "Browsersprache automatisch oder dauerhafte manuelle Auswahl.", language: "Sprache", autoBrowser: "Auto — Browsersprache", repositoryInfo: "Repository und Fine-grained Token.", repository: "Repository",
      aiProviders: "KI-Anbieter", providersInfo: "Wähle den aktiven Dienst. Für jeden Anbieter kann ein eigener Schlüssel sicher gespeichert werden.", activeProvider: "Aktiver Anbieter", customProvider: "Andere / Benutzerdefiniert", model: "Modell",
      localModel: "Lokales 1,5B-Modell", localModelInfo: "Kostenlos und ohne Cloud-API-Schlüssel. Ollama muss auf diesem Computer laufen.", ollamaUrl: "Lokale Ollama-URL",
      backgroundVoice: "Hintergrundsprache", voiceInfo: "Wähle die Sprache des passenden Vosk-Modells, Aktivierungsphrasen und TTS-Stimme.", recognitionLanguage: "Erkennungssprache", wakePhrases: "Aktivierungsphrasen",
      commaSeparated: "Kommagetrennt", voskPath: "Pfad zum Vosk-Modell", ttsVoice: "TTS-Stimme", branchLock: "⌾ GitHub schreibt nur nach", save: "Speichern", auto: "Auto", uiLanguage: "Oberflächensprache",
      createExample: "Zum Beispiel: Pause machen", whatRemind: "Woran soll ich erinnern?", eventName: "Terminname", noteText: "Notiztext", extraDetails: "Weitere Details…", leaveBlank: "Leer lassen, um nichts zu ändern",
      openMenu: "Menü öffnen", clearDialog: "Dialog leeren", quickNote: "Schnelle Notiz", commandPlaceholder: "Befehl schreiben oder sprechen…", commandAria: "Befehl für Dschinni", voiceInput: "Spracheingabe", send: "Senden",
      createAction: "Erstellen", saved: "· gespeichert", missing: "· nicht gesetzt", you: "Du", youAvatar: "DU", agentAvatar: "DS", error: "Fehler", noDate: "Ohne Datum", timeArrived: "jetzt fällig",
      completed: "Erledigt", delete: "Löschen", emptyAgenda: "Hier ist noch alles frei", emptyAgendaHint: "Erstelle Timer, Erinnerung oder Notiz", noPlans: "Noch nichts geplant", creating: "Wird erstellt…", saving: "Wird gespeichert…",
      created: "{item} erstellt.", markedDone: "Als erledigt markiert.", itemDeleted: "Eintrag gelöscht.", systemApp: "Systemanwendung", addedByYou: "Von dir hinzugefügt", notFound: "Nicht gefunden", open: "Öffnen", unavailable: "Nicht verfügbar",
      application: "Anwendung", opening: "Ich öffne „{name}“.", appAdded: "Anwendung hinzugefügt.", appRemoved: "Anwendung aus der Liste entfernt.", confirmDeleteApp: "Anwendung aus Dschinni entfernen?", settingsSaved: "Einstellungen gespeichert.",
      githubConnected: "GitHub verbunden.", configureGithub: "Repository und GitHub-Token eingeben.", notifUnsupported: "nicht unterstützt", notifAllowed: "erlaubt", notifBlocked: "blockiert", browserNotifUnsupported: "Dieser Browser unterstützt keine Systembenachrichtigungen.",
      notifEnabled: "Benachrichtigungen aktiviert.", notifDenied: "Berechtigung wurde nicht erteilt.", notifRequestFailed: "Benachrichtigungsberechtigung konnte nicht angefragt werden.", recognitionUnsupported: "Spracherkennung wird nicht unterstützt",
      allowMicrophone: "Mikrofonzugriff erlauben.", noSpeech: "Keine Sprache erkannt.", speechUnavailable: "Spracherkennung ist nicht verfügbar.", microphoneError: "Mikrofonfehler: {error}", wakeListening: "Warte auf „{phrase}“",
      wakeHeard: "Aktivierungsphrase erkannt — Befehl sprechen…", wakeOn: "Hintergrund-Erkennung aktiviert.", wakeOff: "Hintergrund-Erkennung deaktiviert.", ready: "bereit", notInstalled: "nicht installiert", local: "lokal", noBrowserVoice: "nicht im Browser",
      needsCheck: "Prüfung erforderlich", serverUnavailable: "Server nicht erreichbar", serverInvalid: "Der Server hat eine ungültige Antwort geliefert ({status}).", serverTimeout: "Der Server hat nicht rechtzeitig geantwortet.", httpError: "HTTP-Fehler {status}",
      nameOptional: "Name (optional)", createLabel: "Erstellen: {item}", dayShort: "T", hourShort: "Std.", minuteShort: "Min.",
      sections: "Bereiche", appNameExample: "Zum Beispiel Figma", appPathExample: "C:\\Program Files\\App\\app.exe oder /usr/bin/app",
      apiKey: "API-Schlüssel", baseUrl: "Basis-URL", githubToken: "GitHub-Token", live: "LIVE",
      primaryModel: "Primärmodell", economyModel: "Sparmodell", localJinnModel: "Lokales Jinn-1,5B-Modell",
      localJinnInfo: "Kostenlos ohne Cloud-API-Schlüssel. Ollama und das lokale jinn-Modell sind erforderlich.", advancedAi: "Erweiterte KI-Konfiguration",
      advancedAiInfo: "Sparrouting, Generierungsparameter und begrenzte Suche. Suchausschnitte gelten als nicht vertrauenswürdige Daten.", economyRoute: "Immer das Sparmodell verwenden",
      timeoutSeconds: "Zeitlimit, Sekunden", temperature: "Temperatur", topP: "Top P", maxTokens: "Maximale Token", frequencyPenalty: "Häufigkeitsstrafe",
      searchResults: "Suchergebnisse", webSearch: "Lokaler Jinn darf im Internet suchen", appearance: "Darstellung", appearanceInfo: "Diese Einstellungen werden nur in deinem Browser gespeichert.",
      theme: "Design", systemTheme: "Wie im System", darkTheme: "Dunkel", lightTheme: "Hell", accent: "Akzent", violet: "Violett", cyan: "Cyan", amber: "Bernstein",
      density: "Dichte", comfortable: "Komfortabel", compact: "Kompakt", animation: "Animation", reduced: "Reduziert", solution: "Lösung",
      timerFinished: "Timer beendet", eventStarting: "Termin beginnt",
    },
    es: {
      appTitle: "Genio · Agente personal", appDescription: "Genio — asistente personal local", agent: "Genio", brand: "GENIO", personalAgent: "AGENTE PERSONAL", agentActive: "Agente activo", yourTime: "TU TIEMPO", quickAccess: "ACCESO RÁPIDO", workspace: "ESPACIO DE TRABAJO", close: "Cerrar", dueRequired: "Indica la fecha y la hora.",
      dialog: "Diálogo", planner: "Planificador", apps: "Aplicaciones", quickCreate: "CREACIÓN RÁPIDA", timer: "Temporizador", reminder: "Recordatorio", event: "Evento", note: "Nota",
      timers: "Temporizadores", reminders: "Recordatorios", events: "Eventos", notes: "Notas", notifications: "Notificaciones", enable: "activar", settings: "Ajustes", localMode: "Modo local",
      dialogWith: "Diálogo con Genio", localSecure: "Local y seguro", readyCommands: "listo para órdenes", clear: "Limpiar", yourAgent: "TU AGENTE PERSONAL", greetingDay: "Buenos días.", whatNext: "¿Qué hacemos?",
      welcomeDescription: "Habla con naturalidad: entenderé la orden, crearé un plan o simplemente conversaremos.", timer10: "Temporizador de 10 minutos", timeControl: "Control del tiempo", remindTomorrow: "Recordar mañana",
      forgetNothing: "No olvidar nada", openApp: "Abrir una aplicación", quickLaunch: "Inicio rápido", genieAbilities: "Capacidades de Genio", meet: "Conocerlo", listening: "Escuchando…", sendHint: "enviar ·", newLine: "nueva línea",
      schedule: "AGENDA", upcoming: "Próximas tareas", all: "Todo", plans: "Planes", calendar: "CALENDARIO", today: "Hoy", mon: "Lun", tue: "Mar", wed: "Mié", thu: "Jue", fri: "Vie", sat: "Sáb", sun: "Dom",
      exportCalendar: "Exportar calendario .ics", localLaunch: "INICIO LOCAL", appsDescription: "Abre por voz o con un clic. Las órdenes se ejecutan sin shell.", addApp: "Añadir aplicación", onlyComputer: "Solo en este ordenador",
      remoteBlocked: "El inicio y la configuración de aplicaciones están bloqueados en conexiones remotas.", githubWorkspace: "COPILOTO PARA EL REPOSITORIO GITHUB", repoNotSet: "Repositorio no configurado",
      githubDescription: "Revisa el proyecto y añade texto a archivos con órdenes de voz. Todos los cambios van estrictamente a", connect: "Conectar", reconnect: "Reconectar", githubEvents: "Novedades de GitHub", issues: "Issues",
      openIssues: "Issues abiertos", mergeRequests: "Solicitudes de fusión", lastWorkflow: "Último workflow", commits: "Commits", lastChanges: "Últimos cambios", now: "AHORA", nextTask: "Próxima tarea", freePlan: "Plan libre",
      rest: "Puedes descansar un poco", activity: "ACTIVIDAD", myDay: "Mi día", systemReady: "Sistema listo", plannerRunning: "Planificador activo", openConversation: "Conversación libre", voice: "Voz",
      speakAnswers: "Leer respuestas", wakePhrase: "Frase de activación", microphoneOff: "Micrófono apagado", newEntry: "NUEVO ELEMENTO", create: "Crear", name: "Nombre", duration: "Duración", unit: "Unidad",
      minutes: "Minutos", seconds: "Segundos", hours: "Horas", days: "Días", dateTime: "Fecha y hora", description: "Descripción", cancel: "Cancelar", secureLaunch: "INICIO SEGURO",
      appPathInfo: "Indica una ruta absoluta al ejecutable. No se admiten argumentos ni órdenes de shell.", executable: "Archivo ejecutable", add: "Añadir", configuration: "CONFIGURACIÓN", genieSettings: "Ajustes de Genio",
      secretsLocal: "Las claves API se guardan solo en el", secretsSuffix: "local y nunca se devuelven al navegador.", interface: "Interfaz", interfaceInfo: "Idioma del navegador automático o selección manual persistente.", language: "Idioma",
      autoBrowser: "Auto — idioma del navegador", repositoryInfo: "Repositorio y token fine-grained.", repository: "Repositorio", aiProviders: "Proveedores de IA", providersInfo: "Elige el servicio activo. Puedes guardar con seguridad una clave distinta para cada proveedor.",
      activeProvider: "Proveedor activo", customProvider: "Otro / personalizado", model: "Modelo", localModel: "Modelo local de 1,5B", localModelInfo: "Gratis y sin clave API en la nube. Se necesita Ollama en este equipo.", ollamaUrl: "URL local de Ollama", backgroundVoice: "Voz en segundo plano", voiceInfo: "Elige el idioma del modelo Vosk correspondiente, las frases de activación y la voz TTS.",
      recognitionLanguage: "Idioma de reconocimiento", wakePhrases: "Frases de activación", commaSeparated: "Separadas por comas", voskPath: "Ruta al modelo Vosk", ttsVoice: "Voz TTS", branchLock: "⌾ GitHub escribe solo en", save: "Guardar",
      auto: "Auto", uiLanguage: "Idioma de la interfaz", createExample: "Por ejemplo, hacer una pausa", whatRemind: "¿Qué debo recordar?", eventName: "Nombre del evento", noteText: "Texto de la nota", extraDetails: "Detalles adicionales…",
      leaveBlank: "Déjalo vacío para no cambiarlo", openMenu: "Abrir menú", clearDialog: "Limpiar diálogo", quickNote: "Nota rápida", commandPlaceholder: "Escribe o di una orden…", commandAria: "Orden para Genio", voiceInput: "Entrada de voz", send: "Enviar",
      createAction: "Crear", saved: "· guardada", missing: "· no definida", you: "Tú", youAvatar: "TÚ", agentAvatar: "GE", error: "Error", noDate: "Sin fecha", timeArrived: "ahora", completed: "Completado", delete: "Eliminar",
      emptyAgenda: "Aquí todavía no hay nada", emptyAgendaHint: "Crea un temporizador, recordatorio o nota", noPlans: "Aún no hay nada planificado", creating: "Creando…", saving: "Guardando…", created: "{item} creado.", markedDone: "Marcado como completado.",
      itemDeleted: "Elemento eliminado.", systemApp: "Aplicación del sistema", addedByYou: "Añadida por ti", notFound: "No encontrada", open: "Abrir", unavailable: "No disponible", application: "Aplicación", opening: "Abriendo «{name}».",
      appAdded: "Aplicación añadida.", appRemoved: "Aplicación eliminada de la lista.", confirmDeleteApp: "¿Eliminar la aplicación de Genio?", settingsSaved: "Ajustes guardados.", githubConnected: "GitHub conectado.", configureGithub: "Indica el repositorio y el token de GitHub.",
      notifUnsupported: "no compatibles", notifAllowed: "permitidas", notifBlocked: "bloqueadas", browserNotifUnsupported: "El navegador no admite notificaciones del sistema.", notifEnabled: "Notificaciones activadas.", notifDenied: "No se concedió el permiso.",
      notifRequestFailed: "No se pudo solicitar el permiso de notificaciones.", recognitionUnsupported: "El reconocimiento de voz no es compatible", allowMicrophone: "Permite el acceso al micrófono.", noSpeech: "No se reconoció voz.", speechUnavailable: "El servicio de voz no está disponible.",
      microphoneError: "Error de micrófono: {error}", wakeListening: "Esperando «{phrase}»", wakeHeard: "Frase detectada: di una orden…", wakeOn: "Escucha en segundo plano activada.", wakeOff: "Escucha en segundo plano desactivada.",
      ready: "listo", notInstalled: "no instalado", local: "local", noBrowserVoice: "no disponible", needsCheck: "Revisión necesaria", serverUnavailable: "Servidor no disponible", serverInvalid: "El servidor devolvió una respuesta no válida ({status}).",
      serverTimeout: "El servidor no respondió a tiempo.", httpError: "Error HTTP {status}", nameOptional: "Nombre (opcional)", createLabel: "Crear: {item}", dayShort: "d", hourShort: "h", minuteShort: "min",
      sections: "Secciones", appNameExample: "Por ejemplo, Figma", appPathExample: "C:\\Program Files\\App\\app.exe o /usr/bin/app",
      apiKey: "Clave API", baseUrl: "URL base", githubToken: "Token de GitHub", live: "EN VIVO",
      primaryModel: "Modelo principal", economyModel: "Modelo económico", localJinnModel: "Modelo Jinn local de 1,5B",
      localJinnInfo: "Gratis y sin clave API en la nube. Se necesitan Ollama y el modelo local jinn.", advancedAi: "Configuración avanzada de IA",
      advancedAiInfo: "Ruta económica, controles de generación y búsqueda limitada. Los fragmentos de búsqueda se tratan como datos no fiables.", economyRoute: "Usar siempre el modelo económico",
      timeoutSeconds: "Tiempo de espera, segundos", temperature: "Temperatura", topP: "Top P", maxTokens: "Máximo de tokens", frequencyPenalty: "Penalización de frecuencia",
      searchResults: "Resultados de búsqueda", webSearch: "Permitir que Jinn local busque en internet", appearance: "Apariencia", appearanceInfo: "Estas preferencias solo se guardan en tu navegador.",
      theme: "Tema", systemTheme: "Como el sistema", darkTheme: "Oscuro", lightTheme: "Claro", accent: "Acento", violet: "Violeta", cyan: "Cian", amber: "Ámbar",
      density: "Densidad", comfortable: "Cómoda", compact: "Compacta", animation: "Animación", reduced: "Reducida", solution: "Cómo solucionarlo",
      timerFinished: "Temporizador finalizado", eventStarting: "El evento comienza",
    },
    fr: {
      appTitle: "Génie · Agent personnel", appDescription: "Génie — assistant personnel local", agent: "Génie", brand: "GÉNIE", personalAgent: "AGENT PERSONNEL", agentActive: "Agent actif", yourTime: "VOTRE TEMPS", quickAccess: "ACCÈS RAPIDE", workspace: "ESPACE DE TRAVAIL", close: "Fermer", dueRequired: "Indiquez la date et l’heure.",
      dialog: "Dialogue", planner: "Planificateur", apps: "Applications", quickCreate: "CRÉATION RAPIDE", timer: "Minuteur", reminder: "Rappel", event: "Événement", note: "Note",
      timers: "Minuteurs", reminders: "Rappels", events: "Événements", notes: "Notes", notifications: "Notifications", enable: "activer", settings: "Réglages", localMode: "Mode local",
      dialogWith: "Dialogue avec Génie", localSecure: "Local et sécurisé", readyCommands: "prêt pour vos commandes", clear: "Effacer", yourAgent: "VOTRE AGENT PERSONNEL", greetingDay: "Bonjour.", whatNext: "Que faisons-nous ?",
      welcomeDescription: "Parlez naturellement : je comprendrai la commande, créerai un plan ou discuterai simplement avec vous.", timer10: "Minuteur de 10 minutes", timeControl: "Maîtriser le temps", remindTomorrow: "Rappeler demain",
      forgetNothing: "Ne rien oublier", openApp: "Ouvrir une application", quickLaunch: "Lancement rapide", genieAbilities: "Capacités de Génie", meet: "Faire connaissance", listening: "J’écoute…", sendHint: "envoyer ·", newLine: "nouvelle ligne",
      schedule: "PROGRAMME", upcoming: "Prochaines tâches", all: "Tout", plans: "Projets", calendar: "CALENDRIER", today: "Aujourd’hui", mon: "Lun", tue: "Mar", wed: "Mer", thu: "Jeu", fri: "Ven", sat: "Sam", sun: "Dim",
      exportCalendar: "Exporter le calendrier .ics", localLaunch: "LANCEMENT LOCAL", appsDescription: "Ouvrez à la voix ou en un clic. Les commandes s’exécutent sans shell.", addApp: "Ajouter une application", onlyComputer: "Uniquement sur cet ordinateur",
      remoteBlocked: "Le lancement et la configuration d’applications sont bloqués depuis une connexion distante.", githubWorkspace: "COPILOTE DU DÉPÔT GITHUB", repoNotSet: "Dépôt non configuré",
      githubDescription: "Vérifiez le projet et ajoutez du texte aux fichiers par commandes vocales. Toutes les modifications vont strictement vers", connect: "Connecter", reconnect: "Reconnecter", githubEvents: "Nouveaux événements GitHub", issues: "Issues",
      openIssues: "Issues ouvertes", mergeRequests: "Demandes de fusion", lastWorkflow: "Dernier workflow", commits: "Commits", lastChanges: "Dernières modifications", now: "MAINTENANT", nextTask: "Prochaine tâche", freePlan: "Programme libre",
      rest: "Profitez d’une petite pause", activity: "ACTIVITÉ", myDay: "Ma journée", systemReady: "Système prêt", plannerRunning: "Planificateur actif", openConversation: "Dialogue libre", voice: "Voix",
      speakAnswers: "Lire les réponses", wakePhrase: "Phrase d’activation", microphoneOff: "Microphone désactivé", newEntry: "NOUVEL ÉLÉMENT", create: "Créer", name: "Nom", duration: "Durée", unit: "Unité",
      minutes: "Minutes", seconds: "Secondes", hours: "Heures", days: "Jours", dateTime: "Date et heure", description: "Description", cancel: "Annuler", secureLaunch: "LANCEMENT SÉCURISÉ",
      appPathInfo: "Indiquez le chemin absolu de l’exécutable. Les arguments et commandes shell ne sont pas pris en charge.", executable: "Fichier exécutable", add: "Ajouter", configuration: "CONFIGURATION", genieSettings: "Réglages de Génie",
      secretsLocal: "Les clés API sont enregistrées uniquement dans le", secretsSuffix: "local et ne sont jamais renvoyées au navigateur.", interface: "Interface", interfaceInfo: "Langue du navigateur automatique ou choix manuel persistant.", language: "Langue",
      autoBrowser: "Auto — langue du navigateur", repositoryInfo: "Dépôt et jeton fine-grained.", repository: "Dépôt", aiProviders: "Fournisseurs d’IA", providersInfo: "Choisissez le service actif. Une clé distincte peut être enregistrée en toute sécurité pour chaque fournisseur.",
      activeProvider: "Fournisseur actif", customProvider: "Autre / personnalisé", model: "Modèle", localModel: "Modèle local 1,5B", localModelInfo: "Gratuit et sans clé API cloud. Ollama doit être installé sur cet ordinateur.", ollamaUrl: "URL locale d’Ollama", backgroundVoice: "Voix en arrière-plan", voiceInfo: "Choisissez la langue du modèle Vosk correspondant, les phrases d’activation et la voix TTS.",
      recognitionLanguage: "Langue de reconnaissance", wakePhrases: "Phrases d’activation", commaSeparated: "Séparées par des virgules", voskPath: "Chemin du modèle Vosk", ttsVoice: "Voix TTS", branchLock: "⌾ GitHub écrit uniquement dans", save: "Enregistrer",
      auto: "Auto", uiLanguage: "Langue de l’interface", createExample: "Par exemple, faire une pause", whatRemind: "Que faut-il rappeler ?", eventName: "Nom de l’événement", noteText: "Texte de la note", extraDetails: "Détails supplémentaires…",
      leaveBlank: "Laissez vide pour ne pas modifier", openMenu: "Ouvrir le menu", clearDialog: "Effacer le dialogue", quickNote: "Note rapide", commandPlaceholder: "Écrivez ou prononcez une commande…", commandAria: "Commande pour Génie", voiceInput: "Saisie vocale", send: "Envoyer",
      createAction: "Créer", saved: "· enregistrée", missing: "· non définie", you: "Vous", youAvatar: "VOUS", agentAvatar: "GÉ", error: "Erreur", noDate: "Sans date", timeArrived: "maintenant", completed: "Terminé", delete: "Supprimer",
      emptyAgenda: "Rien ici pour le moment", emptyAgendaHint: "Créez un minuteur, un rappel ou une note", noPlans: "Rien de prévu pour le moment", creating: "Création…", saving: "Enregistrement…", created: "{item} créé.", markedDone: "Marqué comme terminé.",
      itemDeleted: "Élément supprimé.", systemApp: "Application système", addedByYou: "Ajoutée par vous", notFound: "Introuvable", open: "Ouvrir", unavailable: "Indisponible", application: "Application", opening: "J’ouvre «{name}».",
      appAdded: "Application ajoutée.", appRemoved: "Application retirée de la liste.", confirmDeleteApp: "Retirer cette application de Génie ?", settingsSaved: "Réglages enregistrés.", githubConnected: "GitHub connecté.", configureGithub: "Indiquez le dépôt et le jeton GitHub.",
      notifUnsupported: "non prises en charge", notifAllowed: "autorisées", notifBlocked: "bloquées", browserNotifUnsupported: "Ce navigateur ne prend pas en charge les notifications système.", notifEnabled: "Notifications activées.", notifDenied: "Autorisation non accordée.",
      notifRequestFailed: "Impossible de demander l’autorisation des notifications.", recognitionUnsupported: "La reconnaissance vocale n’est pas prise en charge", allowMicrophone: "Autorisez l’accès au microphone.", noSpeech: "Aucune parole reconnue.", speechUnavailable: "Le service vocal est indisponible.",
      microphoneError: "Erreur du microphone : {error}", wakeListening: "En attente de «{phrase}»", wakeHeard: "Phrase entendue — prononcez une commande…", wakeOn: "Écoute en arrière-plan activée.", wakeOff: "Écoute en arrière-plan désactivée.",
      ready: "prêt", notInstalled: "non installé", local: "local", noBrowserVoice: "absente du navigateur", needsCheck: "Vérification requise", serverUnavailable: "Serveur indisponible", serverInvalid: "Le serveur a renvoyé une réponse invalide ({status}).",
      serverTimeout: "Le serveur n’a pas répondu à temps.", httpError: "Erreur HTTP {status}", nameOptional: "Nom (facultatif)", createLabel: "Créer : {item}", dayShort: "j", hourShort: "h", minuteShort: "min",
      sections: "Sections", appNameExample: "Par exemple, Figma", appPathExample: "C:\\Program Files\\App\\app.exe ou /usr/bin/app",
      apiKey: "Clé API", baseUrl: "URL de base", githubToken: "Jeton GitHub", live: "EN DIRECT",
      primaryModel: "Modèle principal", economyModel: "Modèle économique", localJinnModel: "Modèle Jinn local 1,5B",
      localJinnInfo: "Gratuit et sans clé API cloud. Ollama et le modèle local jinn sont requis.", advancedAi: "Configuration IA avancée",
      advancedAiInfo: "Routage économique, paramètres de génération et recherche limitée. Les extraits de recherche sont traités comme des données non fiables.", economyRoute: "Toujours utiliser le modèle économique",
      timeoutSeconds: "Délai, secondes", temperature: "Température", topP: "Top P", maxTokens: "Nombre maximal de jetons", frequencyPenalty: "Pénalité de fréquence",
      searchResults: "Résultats de recherche", webSearch: "Autoriser Jinn local à chercher sur internet", appearance: "Apparence", appearanceInfo: "Ces préférences sont enregistrées uniquement dans votre navigateur.",
      theme: "Thème", systemTheme: "Comme le système", darkTheme: "Sombre", lightTheme: "Clair", accent: "Accent", violet: "Violet", cyan: "Cyan", amber: "Ambre",
      density: "Densité", comfortable: "Confortable", compact: "Compacte", animation: "Animation", reduced: "Réduite", solution: "Solution",
      timerFinished: "Minuteur terminé", eventStarting: "L’événement commence",
    },
  };

  const attributeSources = {
    "Джинн — главная": "appDescription", "Язык интерфейса": "uiLanguage", "Открыть меню": "openMenu",
    "Создать": "createAction", "Очистить диалог": "clearDialog", "Быстрая заметка": "quickNote",
    "Напишите или произнесите команду…": "commandPlaceholder", "Команда для Джинна": "commandAria",
    "Голосовой ввод": "voiceInput", "Отправить": "send", "Например, сделать перерыв": "createExample",
    "Что напомнить?": "whatRemind", "Название события": "eventName", "Текст заметки": "noteText",
    "Дополнительные детали…": "extraDetails", "Оставьте пустым, чтобы не менять": "leaveBlank", "Через запятую": "commaSeparated",
    "Разделы": "sections", "Например, Figma": "appNameExample",
    "C:\\Program Files\\App\\app.exe или /usr/bin/app": "appPathExample",
  };
  const reverse = new Map(Object.entries(copy.ru).map(([key, value]) => [value, key]));
  const reverseAny = new Map();
  Object.values(copy).forEach((dictionary) => {
    Object.entries(dictionary).forEach(([key, value]) => reverseAny.set(value, key));
  });
  const textNodes = [];
  const attributes = [];
  const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const source = node.nodeValue.trim();
    if (source && reverse.has(source)) textNodes.push({ node, original: node.nodeValue, source });
  }
  document.querySelectorAll("[placeholder], [title], [aria-label]").forEach((element) => {
    ["placeholder", "title", "aria-label"].forEach((name) => {
      const source = element.getAttribute(name);
      if (source && (attributeSources[source] || reverse.has(source))) attributes.push({ element, name, source });
    });
  });

  function browserLanguage() {
    const candidates = navigator.languages?.length ? navigator.languages : [navigator.language];
    for (const candidate of candidates) {
      const code = String(candidate || "").split("-", 1)[0].toLowerCase();
      if (languages.includes(code)) return code;
    }
    return "en";
  }
  function safeGet(key) { try { return localStorage.getItem(key); } catch (_) { return null; } }
  function safeSet(key, value) { try { localStorage.setItem(key, value); } catch (_) { /* private mode */ } }

  let selection = safeGet("genie-language") || "auto";
  if (!["auto", ...languages].includes(selection)) selection = "auto";
  let locale = selection === "auto" ? browserLanguage() : selection;

  function t(key, variables = {}) {
    let value = copy[locale]?.[key] ?? copy.ru[key] ?? key;
    Object.entries(variables).forEach(([name, replacement]) => {
      value = value.replaceAll(`{${name}}`, String(replacement));
    });
    return value;
  }

  function translateSubtree(root) {
    if (!root) return;
    const subtreeWalker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let textNode;
    while ((textNode = subtreeWalker.nextNode())) {
      const source = textNode.nodeValue.trim();
      const key = reverseAny.get(source);
      if (source && key) textNode.nodeValue = textNode.nodeValue.replace(source, t(key));
    }
    root.querySelectorAll?.("[placeholder], [title], [aria-label]").forEach((element) => {
      ["placeholder", "title", "aria-label"].forEach((name) => {
        const source = element.getAttribute(name);
        const key = attributeSources[source] || reverseAny.get(source);
        if (source && key) element.setAttribute(name, t(key));
      });
    });
  }

  function translateDocument() {
    textNodes.forEach((entry) => {
      const key = reverse.get(entry.source);
      const translated = copy[locale]?.[key] ?? copy.ru[key];
      entry.node.nodeValue = entry.original.replace(entry.source, translated);
    });
    attributes.forEach((entry) => {
      const key = attributeSources[entry.source] || reverse.get(entry.source);
      entry.element.setAttribute(entry.name, copy[locale]?.[key] ?? copy.ru[key]);
    });
    document.documentElement.lang = locale;
    document.title = t("appTitle");
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.content = t("appDescription");
    const selector = document.querySelector("#language-selector");
    if (selector) selector.value = selection;
  }

  function setLocale(value, { persist = true } = {}) {
    const requested = ["auto", ...languages].includes(value) ? value : "auto";
    selection = requested;
    locale = requested === "auto" ? browserLanguage() : requested;
    if (persist) safeSet("genie-language", requested);
    translateDocument();
    window.dispatchEvent(new CustomEvent("genie:languagechange", { detail: { locale, selection } }));
  }

  window.GenieI18n = {
    t,
    setLocale,
    translateDocument,
    translateSubtree,
    get locale() { return locale; },
    get selection() { return selection; },
    hasSavedSelection() { return safeGet("genie-language") !== null; },
    supported: [...languages],
  };
  translateDocument();
})();
