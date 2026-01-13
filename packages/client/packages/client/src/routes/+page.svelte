<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Send, Bot, User, Loader2, Search, Globe, Database, FileText, Zap } from 'lucide-svelte';

  interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
  }

  let messages: Message[] = $state([]);
  let inputValue = $state('');
  let socket: WebSocket | null = null;
  let isConnected = $state(false);
  let isGenerating = $state(false);
  let chatContainer: HTMLDivElement = $state();
  let agentId = 'research-session';

  // Example prompts for users
  const examplePrompts = [
    "Research the latest developments in quantum computing",
    "Search for news about AI regulations in 2024",
    "What are the current trends in renewable energy?",
    "Find information about SpaceX's recent launches"
  ];

  onMount(() => {
    if (!localStorage.getItem('research_session_id')) {
      localStorage.setItem('research_session_id', 'user-' + Math.random().toString(36).substring(2, 9));
    }
    agentId = localStorage.getItem('research_session_id') || 'default';
    connect();
  });

  onDestroy(() => {
    if (socket) {
      socket.close();
    }
  });

  function connect() {
    const wsUrl = `ws://localhost:8080/agent/${agentId}/ws`;
    console.log('Connecting to', wsUrl);
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('Connected to Research Agent');
      isConnected = true;
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleServerMessage(data);
      } catch (e) {
        // Plain text fallback
        handleServerMessage({ type: 'ai_chunk', content: event.data });
      }
    };

    socket.onclose = () => {
      console.log('Disconnected');
      isConnected = false;
      setTimeout(connect, 3000);
    };

    socket.onerror = (err) => {
      console.error('WebSocket error:', err);
    };
  }

  function handleServerMessage(data: any) {
    const timestamp = Date.now();

    if (data.type === 'system') {
      messages = [...messages, { role: 'system', content: data.content, timestamp }];
    } else if (data.type === 'ai_start') {
      isGenerating = true;
      messages = [...messages, { role: 'assistant', content: '', timestamp }];
    } else if (data.type === 'ai_chunk') {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.content += data.content;
        messages = [...messages];
      }
    } else if (data.type === 'ai_end') {
      isGenerating = false;
    } else if (data.type === 'error') {
      messages = [...messages, { role: 'system', content: `❌ ${data.content}`, timestamp }];
      isGenerating = false;
    }

    scrollToBottom();
  }

  function sendMessage(text?: string) {
    const messageText = text || inputValue;
    if (!messageText.trim() || !socket || !isConnected) return;

    messages = [...messages, { role: 'user', content: messageText, timestamp: Date.now() }];
    socket.send(messageText);
    inputValue = '';
    scrollToBottom();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function scrollToBottom() {
    setTimeout(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 10);
  }

  // Simple markdown-like formatting
  function formatContent(content: string): string {
    return content
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Headers
      .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
      .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-4 mb-2">$1</h2>')
      .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-4 mb-3">$1</h1>')
      // Lists
      .replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>')
      .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4"><span class="font-medium">$1.</span> $2</li>')
      // URLs
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" class="text-blue-400 hover:underline break-all">$1</a>')
      // Code blocks
      .replace(/`([^`]+)`/g, '<code class="bg-gray-700 px-1 rounded text-sm">$1</code>')
      // Line breaks
      .replace(/\n/g, '<br>');
  }
</script>

<div class="flex flex-col h-screen bg-gray-950 text-gray-100 font-sans">
  <!-- Header -->
  <header class="flex items-center justify-between px-6 py-4 bg-gray-900 border-b border-gray-800">
    <div class="flex items-center gap-3">
      <div class="p-2 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl">
        <Search size={22} class="text-white" />
      </div>
      <div>
        <h1 class="text-lg font-bold text-white">Research Intelligence Agent</h1>
        <p class="text-xs text-gray-400 flex items-center gap-2">
          <span class={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
          {isConnected ? 'Connected' : 'Connecting...'}
        </p>
      </div>
    </div>

    <!-- Capabilities badges -->
    <div class="hidden md:flex items-center gap-2">
      <span class="px-2 py-1 bg-gray-800 rounded-full text-xs flex items-center gap-1">
        <Globe size={12} class="text-blue-400" /> Web Search
      </span>
      <span class="px-2 py-1 bg-gray-800 rounded-full text-xs flex items-center gap-1">
        <FileText size={12} class="text-green-400" /> Page Reader
      </span>
      <span class="px-2 py-1 bg-gray-800 rounded-full text-xs flex items-center gap-1">
        <Database size={12} class="text-purple-400" /> Knowledge Base
      </span>
    </div>
  </header>

  <!-- Chat Area -->
  <main class="flex-1 overflow-hidden relative flex flex-col">
    <div
      bind:this={chatContainer}
      class="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth max-w-5xl mx-auto w-full"
    >
      {#if messages.length === 0}
        <div class="h-full flex flex-col items-center justify-center text-center p-10">
          <div class="p-4 bg-gradient-to-br from-purple-600/20 to-blue-600/20 rounded-2xl mb-6">
            <Zap size={48} class="text-purple-400" />
          </div>
          <h2 class="text-2xl font-bold mb-2">Research Intelligence Agent</h2>
          <p class="text-gray-400 mb-8 max-w-md">
            I can search the web, read articles, track news, and build a knowledge base.
            Ask me to research any topic.
          </p>

          <!-- Example prompts -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
            {#each examplePrompts as prompt}
              <button
                onclick={() => sendMessage(prompt)}
                class="text-left p-4 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded-xl transition-colors text-sm"
              >
                <span class="text-gray-400">→</span> {prompt}
              </button>
            {/each}
          </div>
        </div>
      {/if}

      {#each messages as message}
        <div class={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          {#if message.role !== 'user'}
            <div class={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              message.role === 'system'
                ? 'bg-purple-900/50 text-purple-300'
                : 'bg-gradient-to-br from-purple-600 to-blue-600 text-white'
            }`}>
              <Bot size={18} />
            </div>
          {/if}

          <div class={`max-w-[85%] rounded-2xl px-5 py-4 ${
            message.role === 'user'
              ? 'bg-blue-600 text-white rounded-br-sm'
              : message.role === 'system'
                ? 'bg-gray-900 text-gray-300 border border-gray-800 text-sm'
                : 'bg-gray-900 text-gray-100 border border-gray-800 rounded-bl-sm'
          }`}>
            <div class="leading-relaxed prose prose-invert prose-sm max-w-none">
              {@html formatContent(message.content)}
            </div>
          </div>

          {#if message.role === 'user'}
            <div class="w-10 h-10 rounded-xl bg-gray-800 flex items-center justify-center flex-shrink-0 text-gray-300">
              <User size={18} />
            </div>
          {/if}
        </div>
      {/each}

      {#if isGenerating}
        <div class="flex gap-4 justify-start">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center flex-shrink-0 text-white">
            <Bot size={18} />
          </div>
          <div class="bg-gray-900 border border-gray-800 rounded-2xl rounded-bl-sm px-5 py-4 flex items-center gap-3">
            <Loader2 size={18} class="animate-spin text-purple-400" />
            <span class="text-sm text-gray-400">Researching...</span>
          </div>
        </div>
      {/if}
    </div>

    <!-- Input Area -->
    <div class="p-4 border-t border-gray-900 bg-gray-950">
      <div class="max-w-4xl mx-auto">
        <div class="relative">
          <textarea
            bind:value={inputValue}
            onkeydown={handleKeydown}
            placeholder="Ask me to research anything..."
            class="w-full bg-gray-900 text-white placeholder-gray-500 border border-gray-800 rounded-xl py-4 pl-5 pr-14 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 resize-none min-h-[56px] max-h-[200px]"
            rows="1"
          ></textarea>
          <button
            onclick={() => sendMessage()}
            disabled={!inputValue.trim() || !isConnected}
            class="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <Send size={18} />
          </button>
        </div>
        <p class="text-center text-xs text-gray-600 mt-3">
          Powered by ai-query • Tavily Search • Gemini 2.0 Flash
        </p>
      </div>
    </div>
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background-color: #030712;
  }

  :global(h1), :global(h2), :global(h3) {
    margin: 0;
  }

  :global(li) {
    list-style-type: disc;
  }
</style>
