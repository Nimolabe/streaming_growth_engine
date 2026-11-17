// Nachbau von firebase-app.js für die Browser-Tests (kein Netz, kein echtes Firebase).
export function initializeApp(options = {}, name = "[DEFAULT]") {
  return { name, options, automaticDataCollectionEnabled: false };
}
export function getApp() {
  return { name: "[DEFAULT]", options: {} };
}
