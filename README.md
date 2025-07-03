# JIMBODASH - Enhanced AI Chat System

## 🚀 Rozszerzenia AI Chat

Dodano zaawansowany system AI Chat z wieloma providerami, historią konwersacji i streamingiem w czasie rzeczywistym.

## ✨ Nowe Funkcje

### 🤖 Multiple AI Providers

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 (opus, sonnet, haiku)
- **Google**: Gemini Pro
- **Ollama**: Lokalne modele
- **Local**: Własne modele (.bin, .gguf)

### 💬 Chat Features

- **Real-time streaming** responses
- **Conversation history** persistence
- **Model switching** w UI
- **Export conversations** (JSON/TXT)
- **Multi-conversation** management
- **Enhanced UI** z glassmorphism

### 🔧 API Endpoints

#### Chat API

- `POST /api/chat/send` - Wyślij wiadomość
- `GET /api/chat/conversations` - Lista konwersacji
- `POST /api/chat/conversations` - Nowa konwersacja
- `GET /api/chat/conversations/{id}` - Historia konwersacji
- `DELETE /api/chat/conversations/{id}` - Usuń konwersację
- `GET /api/chat/conversations/{id}/export` - Export konwersacji
- `GET /api/chat/models` - Dostępne modele
- `GET /api/chat/config` - Konfiguracja chat

#### AI Management

- `GET /api/ai/list_models` - Lista modeli Ollama/local
- `POST /api/ai/install_model` - Instaluj model
- `GET /api/config/ai` - Pobierz konfigurację
- `POST /api/config/ai` - Zapisz konfigurację

## 🛠️ Instalacja

### 1. Zainstaluj zależności

```bash
cd backend
pip install -r requirements.txt
```

### 2. Opcjonalne AI providers

```bash
# Dla Anthropic
pip install anthropic

# Dla Google
pip install google-generativeai

# Dla Ollama (jeśli nie jest zainstalowany)
curl -fsSL https://ollama.ai/install.sh | sh
```

### 3. Konfiguracja API Keys

1. Otwórz dashboard
2. Kliknij na "AI Assistant" w headerze chat widget
3. Wprowadź swoje API keys dla wybranych providerów

### 4. Uruchom serwer

```bash
cd backend
python server.py
```

## 🎯 Użytkowanie

### Basic Chat

1. Użyj chat widget w prawym dolnym rogu
2. Kliknij ikonę expand aby otworzyć pełny interfejs

### Enhanced Chat

1. Kliknij expand button w chat widget
2. Wybierz model z dropdown
3. Włącz/wyłącz streaming
4. Zarządzaj konwersacjami w sidebar

### Przełączanie Modeli

- Wybierz provider:model z dropdown
- Model automatycznie się zmieni dla nowych wiadomości
- Historia zachowuje informację o używanym modelu

### Export Konwersacji

1. Wybierz konwersację
2. Kliknij "Export" button
3. Wybierz format (JSON/TXT)
4. Plik zostanie pobrany

## 🔧 Rozwiązywanie Problemów

### Błąd 500 w /api/system/resources - NAPRAWIONY ✅

- Dodano lepsze error handling
- Graceful fallback dla brakujących GPU
- Poprawne obsługiwanie Windows paths

### Brak odpowiedzi AI

1. Sprawdź API keys w konfiguracji
2. Sprawdź czy wybrany model jest dostępny
3. Sprawdź logi serwera w terminalu

### Streaming nie działa

1. Upewnij się że provider wspiera streaming
2. Sprawdź połączenie internetowe
3. Spróbuj wyłączyć/włączyć streaming toggle

## 📁 Struktura Plików

```
├── backend/
│   ├── chatbot.py          # ✨ Enhanced AI Chat class
│   ├── server.py           # ✨ Extended API endpoints
│   └── requirements.txt    # ✨ Updated dependencies
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── dashboard.css # ✨ Enhanced chat styles
│   │   └── js/
│   │       ├── dashboard.js  # ✨ Updated integration
│   │       └── chat.js       # ✨ New chat system
│   └── templates/
│       └── dashboard.html    # ✨ Enhanced chat UI
├── config/
│   └── config.json          # ✨ AI configuration
└── data/
    └── chat_history.db      # ✨ SQLite chat history
```

## 🌟 Features Showcase

- **Professional 3D Background** with Three.js
- **Glassmorphism UI** design
- **Real-time AI Chat** with multiple providers
- **Conversation Management** system
- **System Monitoring** dashboard
- **AI Tools CRUD** interface
- **Weather Integration**
- **Network Statistics**

## 🚀 Next Steps

1. Add voice input/output
2. File upload for chat context
3. AI image generation integration
4. Plugin system for custom AI tools
5. Multi-user support
6. Cloud synchronization

---

**Status**: ✅ Production Ready
**Version**: 2.0.0 Enhanced
**Last Updated**: 2025-07-02