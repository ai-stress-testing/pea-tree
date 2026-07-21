import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";
import { actions } from "./store";

createApp(App).mount("#app");

// Probe Ollama on load so the UI can show connection state immediately.
actions.refreshModels();
