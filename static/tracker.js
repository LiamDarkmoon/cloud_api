(async () => {
  const script = document.currentScript;
  const ApiKey = script.getAttribute("data-api-key");
  if (!ApiKey) {
    console.warn("Tracker disabled: missing API key");
    return;
  }

  console.log("Tracker ready and watching for events");

  const API_URL = "https://api-cloudboard.vercel.app/events/track"; // track endpoint de la API
  const DOMAIN = window.location.hostname;
  const PATHNAME = window.location.pathname;
  const REFERRER = document.referrer || null;
  const USER_AGENT = navigator.userAgent;
  const SCREEN_WIDTH = window.innerWidth;
  const SCREEN_HEIGHT = window.innerHeight;
  const PAGE_START = performance.now(); // Tiempo de inicio de la página

  const sessionEvents = [];
  const MAX_BATCH_SIZE = 50;
  const FLUSH_INTERVAL = 60000; // 1min
  const CLICKABLE = `
  button,
  a,
  input,
  select,
  textarea,
  [role="button"],
  [role="link"],
  [data-track],
  [onclick]
`;

  // Sesión persistente mientras el usuario tenga la pestaña abierta
  let sessionId = sessionStorage.getItem("tracker_session");
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem("tracker_session", sessionId);
  }

  async function flushEvents(useBeacon = false) {
    if (!sessionEvents.length) return;

    const batch = sessionEvents.splice(0, sessionEvents.length);

    if (useBeacon && navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(batch)], {
        type: "application/json",
      });
      navigator.sendBeacon(API_URL, blob);
      return;
    }

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${ApiKey}`,
        },
        body: JSON.stringify(batch),
      });

      if (!res.ok) console.error("Tracking error:", await res.text());
    } catch (error) {
      sessionEvents.unshift(...batch);
    }
  }

  async function queueEvent(payload) {
    sessionEvents.push(payload);

    if (sessionEvents.length >= MAX_BATCH_SIZE) {
      flushEvents();
    }

    setInterval(() => {
      flushEvents;
    }, FLUSH_INTERVAL);
  }

  async function sendEvent(event, element, data = {}, useBeacon = false) {
    const payload = {
      domain: DOMAIN,
      pathname: PATHNAME,
      referrer: REFERRER,
      user_agent: USER_AGENT,
      screen_width: SCREEN_WIDTH,
      screen_height: SCREEN_HEIGHT,
      session_id: sessionId,
      event_type: event,
      element: element,
      time_spent: (performance.now() - PAGE_START) / 1000,
      ...data,
    };

    await queueEvent(payload);
  }

  // Evento: página cargada
  window.addEventListener("load", () => sendEvent("page_load", PATHNAME));

  // Evento: clicks en botones o enlaces
  document.addEventListener("click", (e) => {
    const target = e.target.closest(CLICKABLE);
    if (target) {
      const tag = target.tagName.toLowerCase();
      const text = target.innerText?.trim().slice(0, 40);
      const name = target.getAttribute("name");
      const aria = target.getAttribute("aria-label");

      const label = text || aria || name; // Prioridad: texto > aria-label > name

      const element = label ? `${tag} "${label}"` : tag;
      sendEvent("click", element);
    }
  });

  // Evento: salida o cierre
  window.addEventListener("beforeunload", () => {
    sendEvent("exit", PATHNAME);
    flushEvents(true); // beacon
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      sendEvent({
        event_type: "page_hidden",
        pathname: PATHNAME,
      });

      flushEvents(true); // beacon
    }

    if (document.visibilityState === "visible") {
      sendEvent({
        event_type: "page_visible",
        pathname: PATHNAME,
      });
    }
  });
})();
