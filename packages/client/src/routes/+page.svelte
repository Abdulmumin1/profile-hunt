<script lang="ts">
  import { goto } from "$app/navigation";
  import {
    Search,
    Users,
    Newspaper,
    Linkedin,
    Twitter,
    Github,
    ArrowUp,
    ArrowRight,
  } from "lucide-svelte";

  let inputValue = $state("");

  function startNewSession() {
    if (!inputValue.trim()) return;

    // Generate a new session ID
    const sessionId = "session-" + Math.random().toString(36).substring(2, 9);

    // Store the initial query to be used when the session page loads
    sessionStorage.setItem(`initial_query_${sessionId}`, inputValue.trim());

    // Navigate to the session
    goto(`/${sessionId}`);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      startNewSession();
    }
  }
</script>

<div class="app">
  <div class="container">
    <div class="hero">
      <h1 class="logo">profile</h1>
      <p class="tagline">OSINT-powered profile research</p>

      <div class="input-box">
        <input
          type="text"
          bind:value={inputValue}
          onkeydown={handleKeydown}
          placeholder="Search for a person..."
          autofocus
        />
        <div class="input-actions">
          <div class="input-left">
            <!-- <button class="chip active">
              <Search size={14} />
              <span>Deep Search</span>
            </button> -->
          </div>
          <button
            class="send-btn"
            onclick={startNewSession}
            disabled={!inputValue.trim()}
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>

      <div class="mode-chips">
        <button class="mode-chip">
          <Linkedin size={14} />
          <span>LinkedIn</span>
        </button>
        <button class="mode-chip">
          <Twitter size={14} />
          <span>Twitter</span>
        </button>
        <button class="mode-chip">
          <Github size={14} />
          <span>GitHub</span>
        </button>
        <button class="mode-chip">
          <Users size={14} />
          <span>All Profiles</span>
        </button>
        <button class="mode-chip">
          <Newspaper size={14} />
          <span>News</span>
        </button>
      </div>
    </div>
  </div>
</div>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: "SF Mono", "Fira Code", "JetBrains Mono", "Consolas", monospace;
    background: #0a0a0a;
    color: #e8e6e3;
    -webkit-font-smoothing: antialiased;
  }

  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .container {
    max-width: 900px;
    width: 100%;
    margin: 0 auto;
    padding: 0 24px;
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .hero {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding-bottom: 60px;
  }

  .logo {
    font-size: 56px;
    font-weight: 300;
    color: #ca37dd;
    margin-bottom: 12px;
    letter-spacing: -2px;
    font-family:
      "SF Pro Display",
      -apple-system,
      sans-serif;
  }

  .tagline {
    font-size: 14px;
    color: #e8e6e3;
    margin-bottom: 48px;
    text-transform: uppercase;
    letter-spacing: 2px;
  }

  .input-box {
    width: 100%;
    max-width: 680px;
    background: #141414;
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
  }

  .input-box:focus-within {
    border-color: #444;
  }

  .input-box input {
    width: 100%;
    background: transparent;
    border: none;
    outline: none;
    font-size: 15px;
    color: #e8e6e3;
    font-family: inherit;
    margin-bottom: 12px;
  }

  .input-box input::placeholder {
    color: #666;
  }

  .input-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .input-left {
    display: flex;
    gap: 8px;
  }

  .chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #1f1f1f;
    border: 1px solid #333;
    border-radius: 20px;
    color: #888;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
    font-family: inherit;
  }

  .chip:hover {
    background: #2a2a2a;
    color: #aaa;
  }

  .chip.active {
    background: #2a2a2a;
    border-color: #444;
    color: #e8e6e3;
  }

  .send-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #d64be8;
    border: none;
    color: #0a0a0a;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
  }

  .send-btn:hover:not(:disabled) {
    background: #fff;
  }

  .send-btn:disabled {
    background: #ca37dd;
    color: #000000;
    cursor: not-allowed;
  }

  .mode-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
    margin-bottom: 48px;
  }

  .mode-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: transparent;
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    color: #888;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s;
    font-family: inherit;
  }

  .mode-chip:hover {
    border-color: #444;
    color: #e8e6e3;
  }

  .features {
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .feature {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    background: #111;
    border: 1px solid #1a1a1a;
    border-radius: 12px;
    min-width: 220px;
  }

  .feature-icon {
    font-size: 24px;
  }

  .feature-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .feature-text strong {
    font-size: 13px;
    font-weight: 600;
    color: #e8e6e3;
  }

  .feature-text span {
    font-size: 11px;
    color: #666;
  }
</style>
