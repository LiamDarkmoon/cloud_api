(() => {
  const API_URL = "https://cloudapi-chi.vercel.app/events/track"; // tu endpoint de FastAPI
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

  // Obtener JWT del localStorage o iniciar sesión para obtener uno nuevo
  async function getJwtToken() {
    let token = localStorage.getItem("jwt_token");

    if (!token) {
      let res = await fetch("https://cloudapi-chi.vercel.app/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          username: "liamdarkmoon@gmail.com",
          password: "0okamisama",
        }),
      });
      const data = await res.json();
      const token = data.access_token;
      localStorage.setItem("jwt_token", token);
    }

    return token;
  }

  // Envío genérico de eventos
  async function sendEvent(event, element, data = {}) {
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
      time_spent: performance.now() / 1000, // segundos desde carga
      ...data,
    };

    // Si el usuario está logueado y tenés JWT almacenado, lo incluís
    const TOKEN = await getJwtToken();

    try {
      await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(TOKEN && { Authorization: `Bearer ${TOKEN}` }),
        },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.error("Tracker error:", err);
    }
  }

  // Evento: página cargada
  window.addEventListener("load", () => {
    sendEvent("page_load", "body");
  });

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
    sendEvent("exit", "window");
  });
})();
