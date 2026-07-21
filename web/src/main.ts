import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";
import { actions } from "./store";

createApp(App).mount("#app");

// Load persisted state (board + run history) and probe Ollama on startup.
actions.init();
