(async () => {
  const script = document.currentScript;
  const ApiKey = script.getAttribute("data-api-key");

  console.log("Tracker ready and watching for events");

  const API_URL = "https://cloudapi-chi.vercel.app/events/track"; // track endpoint de la API
  const DOMAIN = window.location.hostname;
  const PATHNAME = window.location.pathname;
  const REFERRER = document.referrer || null;
  const USER_AGENT = navigator.userAgent;
  const SCREEN_WIDTH = window.innerWidth;
  const SCREEN_HEIGHT = window.innerHeight;

  // Sesión persistente mientras el usuario tenga la pestaña abierta
  let sessionId = sessionStorage.getItem("tracker_session");
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem("tracker_session", sessionId);
  }

  async function sendEvent(event, element, data = {}, useBeacon = false) {
    const sessionEvents = [];

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
      time_spent: performance.now() / 1000,
      ...data,
    };

    if (useBeacon && navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(payload)], {
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
        body: JSON.stringify(payload),
      });

      if (!res.ok) console.error("Tracking error:", await res.text());
      else await res.json();
    } catch (error) {
      console.error("Tracker error:", error);
    }
  }

  // Evento: página cargada
  window.addEventListener("load", () => sendEvent("page_load", PATHNAME));

  // Evento: clicks en botones o enlaces
  document.addEventListener("click", (e) => {
    const target = e.target.closest("button, a, input");
    if (target) {
      const element = target.innerText || target.tagName;
      sendEvent("click", element);
    }
  });

  // Evento: salida o cierre
  window.addEventListener("beforeunload", () => {
    sendEvent("exit", PATHNAME, {}, true);
  });
})();
