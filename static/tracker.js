(async () => {
  console.log("Tracker initialized");

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

  async function fetchToken(url) {
    console.log("Fetching token");
    console.log(url);
    console.log(DOMAIN);
    let res = await fetch(
      url, // url de autenticación o registro
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: {
          domain: JSON.stringify({ domain: DOMAIN }), // dominio a autenticar o registrar
        },
      }
    );
    const data = await res.json();
    const token = data.domain_token;
    if (token) sessionStorage.setItem("domainToken", token); // almacenar token en sessionStorage
    return token;
  }
  // Obtener domainToken del sessionStorage o iniciar sesión para obtener uno nuevo
  async function getDomainToken() {
    const authUrl = "https://cloudapi-chi.vercel.app/auth/domain";

    let token = sessionStorage.getItem("domainToken"); // obtener token almacenado
    console.log(token);

    if (!token) {
      token =
        (await fetchToken(authUrl)) || (await fetchToken(authUrl + "/add"));
    }
    console.log(sadasdasdasd);

    return token;
  }

  async function sendEvent(event, element, data = {}, useBeacon = false) {
    const TOKEN =
      sessionStorage.getItem("domainToken") || (await getDomainToken());

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
          ...(TOKEN && { Authorization: `Bearer ${TOKEN}` }),
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) console.error("Tracker error response:", await res.text());
      else console.log("Tracker OK:", await res.json());
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
