import { Streamlit, RenderData } from "streamlit-component-lib"
type RecognitionConstructor = new () => any

let recognition: any = null
let isListening = false
let currentArgs: any = {}

const root = document.getElementById("root") as HTMLElement

function getSpeechRecognition(): RecognitionConstructor | null {
  const win = window as any
  return win.SpeechRecognition || win.webkitSpeechRecognition || null
}

function sendValue(value: any) {
  Streamlit.setComponentValue(value)
}

function renderUI(args: any) {
  currentArgs = args

  const label = args.label || "🎙️ Voice command"
  const buttonText = args.button_text || "Start listening"
  const stopText = args.stop_text || "Stop"

  root.innerHTML = `
    <style>
      body {
        margin: 0;
        font-family: Inter, Arial, sans-serif;
        color: white;
      }

      .voice-box {
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(15,23,36,0.86);
        border-radius: 14px;
        padding: 12px;
      }

      .voice-label {
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 8px;
      }

      .voice-button {
        width: 100%;
        border: none;
        border-radius: 10px;
        padding: 10px 12px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #2563eb 0%, #60a5fa 100%);
      }

      .voice-button.listening {
        background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
      }

      .voice-status {
        margin-top: 8px;
        font-size: 12px;
        color: #cbd5e1;
        min-height: 18px;
      }

      .voice-warning {
        color: #fbbf24;
        font-size: 12px;
        margin-top: 6px;
      }
    </style>

    <div class="voice-box">
      <div class="voice-label">${label}</div>
      <button id="voiceBtn" class="voice-button ${isListening ? "listening" : ""}">
        ${isListening ? stopText : buttonText}
      </button>
      <div id="voiceStatus" class="voice-status">
        ${isListening ? "Listening..." : "Click and speak a command"}
      </div>
      <div id="voiceWarning" class="voice-warning"></div>
    </div>
  `

  const btn = document.getElementById("voiceBtn") as HTMLButtonElement
  btn.onclick = toggleListening

  Streamlit.setFrameHeight()
}

function toggleListening() {
  if (isListening) {
    stopListening()
  } else {
    startListening()
  }
}

function startListening() {
  const SpeechRecognition = getSpeechRecognition()

  if (!SpeechRecognition) {
    sendValue({
      transcript: "",
      confidence: 0,
      is_final: false,
      error: "SpeechRecognition is not supported in this browser. Try Chrome or Edge.",
      ts: Date.now(),
    })

    const warning = document.getElementById("voiceWarning")
    if (warning) {
      warning.innerText = "Speech recognition is not supported. Try Chrome or Edge."
    }
    return
  }

  recognition = new SpeechRecognition()
  recognition.lang = currentArgs.lang || "en-US"
  recognition.continuous = false
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  recognition.onstart = () => {
    isListening = true
    renderUI(currentArgs)
  }

  recognition.onresult = (event: any) => {
    const result = event.results[0][0]
    const transcript = result.transcript || ""
    const confidence = result.confidence || 0

    sendValue({
      transcript: transcript.trim(),
      confidence: confidence,
      is_final: true,
      error: null,
      ts: Date.now(),
    })
  }

  recognition.onerror = (event: any) => {
    sendValue({
      transcript: "",
      confidence: 0,
      is_final: false,
      error: event.error || "unknown_error",
      ts: Date.now(),
    })
  }

  recognition.onend = () => {
    isListening = false
    renderUI(currentArgs)
  }

  recognition.start()
}

function stopListening() {
  if (recognition) {
    recognition.stop()
  }
  isListening = false
  renderUI(currentArgs)
}

function onRender(event: Event) {
  const data = (event as CustomEvent<RenderData>).detail
  renderUI(data.args)
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)
Streamlit.setComponentReady()
Streamlit.setFrameHeight()
