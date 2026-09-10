"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

const LANG_KEY = "hd_lang";

export type Lang = "es" | "en";

// Diccionario ES/EN del frontend.
// Añadir claves nuevas aquí conforme se localizan más strings.
export const translations: Record<Lang, Record<string, string>> = {
  es: {
    "app.title": "Gemelo Digital de Humedales Costeros",
    // Navbar
    "nav.dashboard": "Dashboard",
    "nav.scenarios": "Escenarios",
    "nav.measurements": "Mediciones",
    "nav.admin": "Admin",
    "nav.profile": "Perfil",
    "nav.logout": "Salir",
    "nav.login": "Ingresar",
    "nav.profile.title": "Perfil",
    // Toggles
    "lang.toggle": "Cambiar idioma",
    "lang.en": "EN",
    "lang.es": "ES",
    "theme.toggle": "Cambiar tema",
    // Dashboard
    "dash.subtitle":
      "Explora escenarios públicos de restauración y su proyección de retención de carbono. Hipótesis: aumentar ≥ {pct}% de carbono retenido al horizonte.",
    "dash.openRealtime": "Abrir monitoreo en vivo",
    "dash.publicScenarios": "Escenarios públicos",
    "dash.noScenarios": "No hay escenarios públicos disponibles.",
    "dash.simulating": "Simulando…",
    "dash.meetsHypothesis": "Cumple hipótesis (≥{pct}%)",
    "dash.notMeets": "No cumple ({pct}% umbral)",
    "dash.carbonBase": "Carbono base",
    "dash.carbonHorizon": "Carbono horizonte",
    "dash.variation": "Variación",
    "dash.threshold": "Umbral {pct}%",
    "dash.effectiveArea": "Superficie efectiva",
    "dash.projectedChart": "Retención de carbono proyectada (comparativa)",
    "dash.yLabel": "Carbono retenido (t)",
    "dash.researcherCtaPrefix": "¿Eres investigador?",
    "dash.researcherCtaSuffix": "para crear y simular tus propios escenarios.",
    "dash.loginLink": "Inicia sesión",
    // Login
    "login.title": "Iniciar sesión",
    "login.email": "Correo electrónico",
    "login.password": "Contraseña",
    "login.submit": "Ingresar",
    "login.loading": "Ingresando…",
    "login.loggingIn": "Verificando acceso…",
    "login.back": "Volver al inicio",
    "login.crearCuenta": "Crear cuenta",
    "login.accede": "Accede con tu cuenta de investigador.",
    "login.registrateVisitante": "Regístrate como visitante/investigador.",
    "login.nombreCompleto": "Nombre completo",
    "login.institucion": "Institución (opcional)",
    "login.entrar": "Entrar",
    "login.registrarse": "Registrarse",
    "login.noTienesCuenta": "¿No tienes cuenta?",
    "login.yaTienesCuenta": "¿Ya tienes cuenta?",
    "login.registrate": "Regístrate",
    "login.iniciaSesion": "Inicia sesión",
    "login.volverDashboard": "Volver al dashboard",
    // Profile
    "profile.title": "Mi perfil",
    "profile.datos": "Datos de perfil",
    "profile.nombreCompleto": "Nombre completo",
    "profile.correo": "Correo",
    "profile.institucion": "Institución",
    "profile.guardarPerfil": "Guardar perfil",
    "profile.cambiarPassword": "Cambiar contraseña",
    "profile.passwordActual": "Contraseña actual",
    "profile.passwordNueva": "Nueva contraseña",
    "profile.cambiarPasswordBtn": "Cambiar contraseña",
    "profile.actualizado": "Perfil actualizado.",
    "profile.passwordActualizada": "Contraseña actualizada.",
    // Realtime
    "realtime.title": "Monitoreo en vivo",
    "realtime.subtitle": "Flujo de datos del gemelo digital en tiempo real.",
    "realtime.connect": "Conectar",
    "realtime.disconnect": "Desconectar",
    "realtime.connected": "Conectado",
    "realtime.disconnected": "Desconectado",
    "realtime.noData": "Sin datos aún. Conecta para ver el flujo.",
    "realtime.centro": "Centro de monitoreo",
    "realtime.titulo": "Estado del humedal en vivo",
    "realtime.desc":
      "Observa cómo evoluciona el humedal con el escenario seleccionado. Esta primera versión utiliza una señal simulada reproducible.",
    "realtime.escenario": "Escenario",
    "realtime.noEscenariosPub": "No hay escenarios públicos disponibles.",
    "realtime.humedalRef": "Humedal de referencia",
    "realtime.restauracion": "Restauración: {pct}%",
    "realtime.slr": "SLR: {v}",
    "realtime.horizonte": "Horizonte: {v}",
    "realtime.iniciar": "Iniciar",
    "realtime.pausar": "Pausar",
    "realtime.reiniciar": "Reiniciar",
    "realtime.velocidad": "Velocidad",
    "realtime.fuente":
      "Fuente actual: simulada. Los valores representan una reproducción del horizonte del escenario, no lecturas de sensores.",
    "realtime.status.connecting": "Conectando",
    "realtime.status.running": "Ejecutando",
    "realtime.status.paused": "Pausado",
    "realtime.status.completed": "Horizonte alcanzado",
    "realtime.status.disconnected": "Desconectado",
    "realtime.m.carbon": "Carbono retenido",
    "realtime.m.freatico": "Nivel freático",
    "realtime.m.cobertura": "Cobertura vegetal",
    "realtime.m.area": "Superficie efectiva",
    "realtime.chartCS": "Carbono y superficie",
    "realtime.chartCSline": "Carbono retenido (tC)",
    "realtime.chartCSarea": "Superficie efectiva (ha)",
    "realtime.chartFreatico": "Nivel freático",
    "realtime.chartFreaticoLine": "Nivel de agua (m)",
    "realtime.chartCobertura": "Cobertura vegetal",
    "realtime.chartCoberturaName": "Cobertura",
    // Scenarios
    "scenarios.title": "Escenarios",
    "scenarios.new": "Nuevo escenario",
    "scenarios.name": "Nombre",
    "scenarios.save": "Guardar",
    "scenarios.cancel": "Cancelar",
    "scenarios.del": "Eliminar",
    "scenarios.edit": "Editar",
    "scenarios.create": "Crear",
    "scenarios.actions": "Acciones",
    "scenarios.none": "No hay escenarios.",
    "scenarios.editar": "Editar escenario",
    "scenarios.crear": "Crear escenario",
    "scenarios.parametros": "Parámetros",
    "scenarios.chartSerie": "Retención de carbono (serie temporal)",
    "scenarios.chartCobertura": "Cobertura vegetal (%)",
    // Measurements
    "measurements.title": "Mediciones",
    "measurements.nueva": "Nueva medición",
    "measurements.editar": "Editar medición",
    // Admin
    "admin.title": "Administración",
    "admin.usuarios": "Usuarios",
    "admin.calibracion": "Calibración de parámetros del modelo",
    // Errores / misc
    "common.edit": "Editar",
    "common.delete": "Eliminar",
    "common.save": "Guardar",
    "common.cancel": "Cancelar",
    "common.loading": "Cargando…",
    "common.error": "Error",
  },
  en: {
    "app.title": "Coastal Wetlands Digital Twin",
    // Navbar
    "nav.dashboard": "Dashboard",
    "nav.scenarios": "Scenarios",
    "nav.measurements": "Measurements",
    "nav.admin": "Admin",
    "nav.profile": "Profile",
    "nav.logout": "Log out",
    "nav.login": "Sign in",
    "nav.profile.title": "Profile",
    // Toggles
    "lang.toggle": "Switch language",
    "lang.en": "EN",
    "lang.es": "ES",
    "theme.toggle": "Toggle theme",
    // Dashboard
    "dash.subtitle":
      "Explore public restoration scenarios and their carbon retention projection. Hypothesis: increase retained carbon by ≥ {pct}% at the horizon.",
    "dash.openRealtime": "Open live monitoring",
    "dash.publicScenarios": "Public scenarios",
    "dash.noScenarios": "No public scenarios available.",
    "dash.simulating": "Simulating…",
    "dash.meetsHypothesis": "Meets hypothesis (≥{pct}%)",
    "dash.notMeets": "Does not meet ({pct}% threshold)",
    "dash.carbonBase": "Baseline carbon",
    "dash.carbonHorizon": "Horizon carbon",
    "dash.variation": "Variation",
    "dash.threshold": "{pct}% threshold",
    "dash.effectiveArea": "Effective area",
    "dash.projectedChart": "Projected carbon retention (comparison)",
    "dash.yLabel": "Retained carbon (t)",
    "dash.researcherCtaPrefix": "Are you a researcher?",
    "dash.researcherCtaSuffix": "to create and simulate your own scenarios.",
    "dash.loginLink": "Sign in",
    // Login
    "login.title": "Sign in",
    "login.email": "Email",
    "login.password": "Password",
    "login.submit": "Sign in",
    "login.loading": "Signing in…",
    "login.loggingIn": "Verifying access…",
    "login.back": "Back to home",
    "login.crearCuenta": "Create account",
    "login.accede": "Sign in with your researcher account.",
    "login.registrateVisitante": "Register as visitor/researcher.",
    "login.nombreCompleto": "Full name",
    "login.institucion": "Institution (optional)",
    "login.entrar": "Sign in",
    "login.registrarse": "Register",
    "login.noTienesCuenta": "Don't have an account?",
    "login.yaTienesCuenta": "Already have an account?",
    "login.registrate": "Register",
    "login.iniciaSesion": "Sign in",
    "login.volverDashboard": "Back to dashboard",
    // Realtime
    "realtime.title": "Live monitoring",
    "realtime.subtitle": "Real-time data stream from the digital twin.",
    "realtime.connect": "Connect",
    "realtime.disconnect": "Disconnect",
    "realtime.connected": "Connected",
    "realtime.disconnected": "Disconnected",
    "realtime.noData": "No data yet. Connect to see the stream.",
    "realtime.centro": "Monitoring center",
    "realtime.titulo": "Wetland live status",
    "realtime.desc":
      "Watch how the wetland evolves with the selected scenario. This first version uses a reproducible simulated signal.",
    "realtime.escenario": "Scenario",
    "realtime.noEscenariosPub": "No public scenarios available.",
    "realtime.humedalRef": "Reference wetland",
    "realtime.restauracion": "Restoration: {pct}%",
    "realtime.slr": "SLR: {v}",
    "realtime.horizonte": "Horizon: {v}",
    "realtime.iniciar": "Start",
    "realtime.pausar": "Pause",
    "realtime.reiniciar": "Reset",
    "realtime.velocidad": "Speed",
    "realtime.fuente":
      "Current source: simulated. Values are a replay of the scenario horizon, not sensor readings.",
    "realtime.status.connecting": "Connecting",
    "realtime.status.running": "Running",
    "realtime.status.paused": "Paused",
    "realtime.status.completed": "Horizon reached",
    "realtime.status.disconnected": "Disconnected",
    "realtime.m.carbon": "Retained carbon",
    "realtime.m.freatico": "Water table",
    "realtime.m.cobertura": "Vegetation cover",
    "realtime.m.area": "Effective area",
    "realtime.chartCS": "Carbon and area",
    "realtime.chartCSline": "Retained carbon (tC)",
    "realtime.chartCSarea": "Effective area (ha)",
    "realtime.chartFreatico": "Water table",
    "realtime.chartFreaticoLine": "Water level (m)",
    "realtime.chartCobertura": "Vegetation cover",
    "realtime.chartCoberturaName": "Cover",
    // Profile
    "profile.title": "My profile",
    "profile.datos": "Profile data",
    "profile.nombreCompleto": "Full name",
    "profile.correo": "Email",
    "profile.institucion": "Institution",
    "profile.guardarPerfil": "Save profile",
    "profile.cambiarPassword": "Change password",
    "profile.passwordActual": "Current password",
    "profile.passwordNueva": "New password",
    "profile.cambiarPasswordBtn": "Change password",
    "profile.actualizado": "Profile updated.",
    "profile.passwordActualizada": "Password updated.",
    // Scenarios
    "scenarios.title": "Scenarios",
    "scenarios.new": "New scenario",
    "scenarios.name": "Name",
    "scenarios.save": "Save",
    "scenarios.cancel": "Cancel",
    "scenarios.del": "Delete",
    "scenarios.edit": "Edit",
    "scenarios.create": "Create",
    "scenarios.actions": "Actions",
    "scenarios.none": "No scenarios.",
    "scenarios.editar": "Edit scenario",
    "scenarios.crear": "Create scenario",
    "scenarios.parametros": "Parameters",
    "scenarios.chartSerie": "Carbon retention (time series)",
    "scenarios.chartCobertura": "Vegetation cover (%)",
    // Measurements
    "measurements.title": "Measurements",
    "measurements.nueva": "New measurement",
    "measurements.editar": "Edit measurement",
    // Admin
    "admin.title": "Administration",
    "admin.usuarios": "Users",
    "admin.calibracion": "Model parameter calibration",
    // Errores / misc
    "common.edit": "Edit",
    "common.delete": "Delete",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.loading": "Loading…",
    "common.error": "Error",
  },
};

interface I18nContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue>({
  lang: "es",
  setLang: () => {},
  t: (k) => k,
});

function getInitialLang(): Lang {
  if (typeof window === "undefined") return "es";
  const stored = localStorage.getItem(LANG_KEY);
  return stored === "en" || stored === "es" ? stored : "es";
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("es");

  useEffect(() => {
    setLangState(getInitialLang());
  }, []);

  useEffect(() => {
    localStorage.setItem(LANG_KEY, lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l: Lang) => setLangState(l), []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>): string => {
      let s = translations[lang][key] ?? key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          s = s.replace(`{${k}}`, String(v));
        }
      }
      return s;
    },
    [lang],
  );

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}