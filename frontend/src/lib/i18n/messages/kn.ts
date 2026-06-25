/** Kannada (ಕನ್ನಡ). Machine-assisted draft — review by a native speaker before production. */
import type { Messages } from "./en";

const kn: Messages = {
  "voice.eyebrow.listening": "ಆಲಿಸುತ್ತಿದ್ದೇನೆ",
  "voice.eyebrow.thinking": "ಯೋಚಿಸುತ್ತಿದ್ದೇನೆ",
  "voice.eyebrow.done": "ಮುಗಿದಿದೆ",
  "voice.eyebrow.idle": "ವಾಯ್ಸ್ ಸಹಾಯ",

  "voice.headline.listening": "ನಾನು ಆಲಿಸುತ್ತಿದ್ದೇನೆ…",
  "voice.headline.thinking": "ಕೆಲಸ ಮಾಡುತ್ತಿದ್ದೇನೆ…",
  "voice.headline.done": "ನಾನು ಕಂಡುಕೊಂಡದ್ದು ಇಲ್ಲಿದೆ",
  "voice.headline.idle": "ನಿಮ್ಮ ಸಮಸ್ಯೆ ಹೇಳಿ",

  "footer.startRecording": "ರೆಕಾರ್ಡಿಂಗ್ ಪ್ರಾರಂಭಿಸಿ",
  "footer.stopRecording": "ರೆಕಾರ್ಡಿಂಗ್ ನಿಲ್ಲಿಸಿ",
  "footer.send": "ಕಳುಹಿಸಿ",
  "footer.placeholder": "ಯಾವುದೇ ಭಾಷೆಯಲ್ಲಿ ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಟೈಪ್ ಮಾಡಿ…",
  "footer.switchToVoice": "ವಾಯ್ಸ್‌ಗೆ ಬದಲಿಸಿ",
  "footer.switchToText": "ಟೆಕ್ಸ್ಟ್‌ಗೆ ಬದಲಿಸಿ",

  "status.processing": "ಸಂಸ್ಕರಿಸಲಾಗುತ್ತಿದೆ",
  "status.complete": "ಮುಗಿದಿದೆ",
  "status.stage1": "ಆಡಿಯೊ ಸ್ವೀಕರಿಸಲಾಗುತ್ತಿದೆ",
  "status.stage2": "ಉದ್ದೇಶ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲಾಗುತ್ತಿದೆ",
  "status.stage3": "ಆರ್ಡರ್ ನೋಡಲಾಗುತ್ತಿದೆ",
  "status.stage4": "ನೀತಿ ತರಲಾಗುತ್ತಿದೆ",
  "status.stage5": "ಪರಿಹಾರ ನಿರ್ಧರಿಸಲಾಗುತ್ತಿದೆ",
  "status.stage6": "ಎಸ್ಕಲೇಶನ್ ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ",
  "status.stage7": "ಪ್ರತಿಕ್ರಿಯೆ ರಚಿಸಲಾಗುತ್ತಿದೆ",
  "status.stage8": "ಮಾತಿಗೆ ಪರಿವರ್ತಿಸಲಾಗುತ್ತಿದೆ",
  "status.stage9": "ಟಿಕೆಟ್ ರಚಿಸಲಾಗುತ್ತಿದೆ",

  "response.escalated": "ಎಸ್ಕಲೇಟ್ ಮಾಡಲಾಗಿದೆ",
  "response.resolved": "ಪರಿಹರಿಸಲಾಗಿದೆ",
  "response.ticket": "ಟಿಕೆಟ್",
  "response.confidence": "ವಿಶ್ವಾಸ",

  "warning.title": "ವಾಯ್ಸ್ ಗುರುತಿಸುವಿಕೆ ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ.",
  "warning.body": "ಕೆಳಗೆ ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಟೈಪ್ ಮಾಡಿ — ಉಳಿದದ್ದೆಲ್ಲಾ ಸರಿಯಾಗಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ.",

  "error.micDenied": "ಮೈಕ್ರೊಫೋನ್ ಪ್ರವೇಶ ನಿರಾಕರಿಸಲಾಗಿದೆ. ದಯವಿಟ್ಟು ಮೈಕ್ರೊಫೋನ್ ಪ್ರವೇಶ ಅನುಮತಿಸಿ.",
  "error.connection": "ಸಂಪರ್ಕ ದೋಷ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
  "error.connectionLost": "ಹಲವು ಪ್ರಯತ್ನಗಳ ನಂತರ ಸಂಪರ್ಕ ಕಡಿದುಹೋಯಿತು. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
  "error.generic": "ಏನೋ ತಪ್ಪಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
};

export default kn;
