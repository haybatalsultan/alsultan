(() => {
  "use strict";

  let googleMapsPromise = null;

  const selectedDialCode = (select) => {
    if (!select?.options.length) return "";
    const text = select.options[select.selectedIndex]?.text || "";
    const match = text.match(/\(\+(\d{1,4})\)\s*$/);
    return match ? `+${match[1]}` : "";
  };

  const updateDialCode = (scope) => {
    const country = scope.querySelector("[data-country-select]");
    const output = scope.querySelector("[data-dial-code]");
    if (country && output) output.textContent = selectedDialCode(country);
  };

  document.querySelectorAll("[data-phone-country-scope]").forEach((scope) => {
    const country = scope.querySelector("[data-country-select]");
    const phone = scope.querySelector("[data-phone-input]");
    updateDialCode(scope);

    const dial = selectedDialCode(country);
    if (phone && dial && phone.value.startsWith(dial)) {
      phone.value = phone.value.slice(dial.length);
    }
    country?.addEventListener("change", () => updateDialCode(scope));
  });

  const setStatus = (node, message, state = "") => {
    if (!node) return;
    node.textContent = message || "";
    if (state) node.dataset.state = state;
    else delete node.dataset.state;
  };

  const setField = (scope, name, value) => {
    if (value === null || value === undefined || value === "") return false;
    const field = scope.querySelector(`[data-address-field="${name}"]`);
    if (!field) return false;

    // Country fields are selects containing ISO alpha-2 codes. Never inject options.
    if (name === "country" && field.tagName === "SELECT") {
      const normalized = String(value).toUpperCase();
      const exists = Array.from(field.options).some((option) => option.value === normalized);
      if (!exists) return false;
      field.value = normalized;
    } else {
      field.value = String(value);
    }

    field.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  };

  const componentValue = (components, kinds, short = false) => {
    for (const kind of kinds) {
      const component = components.find((item) => item.types?.includes(kind));
      if (component) return short ? component.short_name : component.long_name;
    }
    return "";
  };

  const normalizeGoogleResult = (result) => {
    const components = result?.address_components || [];

    const route = componentValue(components, ["route"]);
    const streetNumber = componentValue(components, ["street_number"]);
    const street = [route, streetNumber].filter(Boolean).join(" ").trim();

    return {
      country: componentValue(components, ["country"], true).toUpperCase(),
      emirate: componentValue(components, ["administrative_area_level_1"]),
      city: componentValue(
        components,
        ["locality", "postal_town", "administrative_area_level_2"]
      ),
      area: componentValue(
        components,
        ["sublocality_level_1", "sublocality", "neighborhood"]
      ),
      street,
      postal_code: componentValue(components, ["postal_code"]),
      formatted_address: result?.formatted_address || "",
    };
  };

  const loadGoogleMaps = (apiKey, language) => {
    if (window.google?.maps?.Geocoder) return Promise.resolve(window.google.maps);
    if (googleMapsPromise) return googleMapsPromise;
    if (!apiKey) return Promise.reject(new Error("maps-key-missing"));

    googleMapsPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      const params = new URLSearchParams({
        key: apiKey,
        v: "weekly",
        language: language === "en" ? "en" : "ar",
      });
      script.src = `https://maps.googleapis.com/maps/api/js?${params.toString()}`;
      script.async = true;
      script.defer = true;
      script.referrerPolicy = "strict-origin-when-cross-origin";
      script.addEventListener("load", () => {
        if (window.google?.maps?.Geocoder) resolve(window.google.maps);
        else reject(new Error("maps-geocoder-unavailable"));
      }, { once: true });
      script.addEventListener("error", () => reject(new Error("maps-load-failed")), { once: true });
      document.head.appendChild(script);
    });

    return googleMapsPromise;
  };

  const reverseGeocodeInBrowser = async (scope, latitude, longitude) => {
    const apiKey = scope.dataset.googleMapsKey || "";
    const language = scope.dataset.googleMapsLanguage || document.documentElement.lang || "ar";
    const maps = await loadGoogleMaps(apiKey, language);
    const geocoder = new maps.Geocoder();
    const response = await geocoder.geocode({
      location: { lat: Number(latitude), lng: Number(longitude) },
    });
    const first = response?.results?.[0];
    if (!first) throw new Error("zero-results");
    return normalizeGoogleResult(first);
  };

  const reverseGeocodeOnServer = async (scope, button, latitude, longitude) => {
    const endpoint = button.dataset.endpoint;
    if (!endpoint) throw new Error("server-geocoder-unavailable");

    const csrf = scope.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
    if (!csrf) throw new Error("csrf-missing");

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "X-CSRFToken": csrf,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: new URLSearchParams({
        latitude: String(latitude),
        longitude: String(longitude),
      }).toString(),
      credentials: "same-origin",
      redirect: "error",
    });

    if (!response.ok) throw new Error("server-reverse-geocoding-failed");
    return response.json();
  };

  const fillAddress = (scope, data) => {
    ["country", "emirate", "city", "area", "street", "postal_code"].forEach((name) => {
      setField(scope, name, data?.[name]);
    });
    updateDialCode(scope);
  };

  const storeCoordinatesInForm = (scope, latitude, longitude) => {
    const latField = scope.querySelector('[data-location-field="latitude"]');
    const lngField = scope.querySelector('[data-location-field="longitude"]');
    if (latField) latField.value = Number(latitude).toFixed(6);
    if (lngField) lngField.value = Number(longitude).toFixed(6);
  };

  const permissionState = async () => {
    if (!navigator.permissions?.query) return "unknown";
    try {
      const result = await navigator.permissions.query({ name: "geolocation" });
      return result?.state || "unknown";
    } catch (_) {
      // Some browsers reject Permissions API queries; geolocation can still be requested by the user.
      return "unknown";
    }
  };

  const getCurrentPositionWithWatchdog = (options, hardTimeoutMs = 9000) =>
    new Promise((resolve, reject) => {
      let settled = false;

      const finish = (fn, value) => {
        if (settled) return;
        settled = true;
        clearTimeout(watchdog);
        fn(value);
      };

      const watchdog = window.setTimeout(() => {
        const error = new Error("geolocation-hard-timeout");
        error.code = 3;
        finish(reject, error);
      }, hardTimeoutMs);

      navigator.geolocation.getCurrentPosition(
        (position) => finish(resolve, position),
        (error) => finish(reject, error),
        options
      );
    });

  document.querySelectorAll("[data-location-scope]").forEach((scope) => {
    const button = scope.querySelector("[data-use-location]");
    const status = scope.querySelector("[data-location-status]");
    if (!button) return;

    button.addEventListener("click", async () => {
      // Privacy: location is requested only after this explicit user action.
      if (!window.isSecureContext && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
        setStatus(
          status,
          button.dataset.insecure || "Location requires a secure HTTPS connection.",
          "error"
        );
        return;
      }

      if (!navigator.geolocation) {
        setStatus(
          status,
          button.dataset.unsupported || "Location is not supported.",
          "error"
        );
        return;
      }

      const permission = await permissionState();
      if (permission === "denied") {
        setStatus(
          status,
          button.dataset.blocked || button.dataset.denied || "Location permission is blocked in your browser.",
          "error"
        );
        return;
      }

      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      setStatus(status, button.dataset.locating || "Locating…", "loading");

      try {
        const position = await getCurrentPositionWithWatchdog(
          {
            enableHighAccuracy: false,
            timeout: 7000,
            maximumAge: 120000,
          },
          9000
        );

        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        // Coordinates remain only in the form until explicit form submission.
        storeCoordinatesInForm(scope, latitude, longitude);

        let address = null;

        if (scope.dataset.googleMapsKey) {
          try {
            address = await Promise.race([
              reverseGeocodeInBrowser(scope, latitude, longitude),
              new Promise((_, reject) =>
                setTimeout(() => reject(new Error("maps-timeout")), 7000)
              ),
            ]);
          } catch (_) {
            address = null;
          }
        }

        if (!address && button.dataset.endpoint) {
          try {
            address = await Promise.race([
              reverseGeocodeOnServer(scope, button, latitude, longitude),
              new Promise((_, reject) =>
                setTimeout(() => reject(new Error("server-geocoder-timeout")), 7000)
              ),
            ]);
          } catch (_) {
            address = null;
          }
        }

        if (address) {
          fillAddress(scope, address);
          setStatus(
            status,
            button.dataset.success || "Location updated. Please review the address.",
            "success"
          );
        } else {
          setStatus(
            status,
            button.dataset.partial || "Coordinates captured. Complete the address manually.",
            "warning"
          );
        }
      } catch (error) {
        let message = button.dataset.unavailable || "Your location is currently unavailable.";
        if (error?.code === 1) {
          message = button.dataset.denied || message;
        } else if (error?.code === 3) {
          message = button.dataset.timeout || message;
        }
        setStatus(status, message, "error");
      } finally {
        button.disabled = false;
        button.removeAttribute("aria-busy");
      }
    });
  });

  document.querySelectorAll("[data-saved-address]").forEach((button) => {
    button.addEventListener("click", () => {
      const scope = button.closest("[data-location-scope]");
      if (!scope) return;

      ["country","emirate","city","area","street","building","apartment_or_villa",
       "postal_code","latitude","longitude"].forEach((name) => {
        const value = button.dataset[name.replaceAll("_", "")];

        if (name === "latitude" || name === "longitude") {
          const field = scope.querySelector(`[data-location-field="${name}"]`);
          if (field && value) field.value = value;
        } else {
          setField(scope, name, value);
        }
      });

      updateDialCode(scope);
    });
  });
})();
