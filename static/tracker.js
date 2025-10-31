(() => {
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

  // Obtener JWT del localStorage o iniciar sesión para obtener uno nuevo
  async function getJwtToken() {
    let token = localStorage.getItem("jwt");

    if (!token) {
      let res = await fetch(
        "https://cloudapi-chi.vercel.app/auth/login", // Iniciar sesión para obtener JWT
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({
            username: "liamdarkmoon@gmail.com", // Cambiar por credenciales reales
            password: "0okamisama",
          }),
        }
      );
      const data = await res.json();
      const token = data.access_token;
      localStorage.setItem("jwt", token);
    }

    return token;
  }

  // Envíar evento
  async function sendEvent(event, element, data = {}) {
    const seconds = performance.now() / 1000;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    const formatted = `${minutes}m ${remainingSeconds}s`;

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
      time_spent: formatted, // minutos y segundos desde carga
      ...data,
    };

    // Usuar JWT almacenado
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
    } catch (error) {
      console.error("Tracker error:", error);
    }
  }

  // Evento: página cargada
  window.addEventListener("load", () => {
    sendEvent("page_load", PATHNAME);
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
    sendEvent("exit", PATHNAME);
  });
})();
