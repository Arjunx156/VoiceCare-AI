/** Hindi (हिन्दी). Machine-assisted draft — review by a native speaker before production. */
import type { Messages } from "./en";

const hi: Messages = {
  "voice.eyebrow.listening": "सुन रहा हूँ",
  "voice.eyebrow.thinking": "सोच रहा हूँ",
  "voice.eyebrow.done": "पूर्ण",
  "voice.eyebrow.idle": "वॉइस सहायता",

  "voice.headline.listening": "मैं सुन रहा हूँ…",
  "voice.headline.thinking": "काम चल रहा है…",
  "voice.headline.done": "यह मुझे मिला",
  "voice.headline.idle": "अपनी समस्या बोलें",

  "footer.startRecording": "रिकॉर्डिंग शुरू करें",
  "footer.stopRecording": "रिकॉर्डिंग रोकें",
  "footer.send": "भेजें",
  "footer.placeholder": "किसी भी भाषा में अपना प्रश्न लिखें…",
  "footer.switchToVoice": "वॉइस पर जाएँ",
  "footer.switchToText": "टेक्स्ट पर जाएँ",
  "footer.newConversation": "नई बातचीत",

  "status.processing": "प्रोसेस हो रहा है",
  "status.complete": "पूर्ण",
  "status.stage1": "ऑडियो प्राप्त हो रहा है",
  "status.stage2": "मंशा समझ रहे हैं",
  "status.stage3": "ऑर्डर देख रहे हैं",
  "status.stage4": "नीति प्राप्त कर रहे हैं",
  "status.stage5": "समाधान तय कर रहे हैं",
  "status.stage6": "एस्केलेशन जाँच रहे हैं",
  "status.stage7": "उत्तर तैयार कर रहे हैं",
  "status.stage8": "वाणी में बदल रहे हैं",
  "status.stage9": "टिकट बना रहे हैं",

  "response.escalated": "एस्केलेट किया गया",
  "response.resolved": "हल हो गया",
  "response.ticket": "टिकट",
  "response.confidence": "विश्वास",

  "warning.title": "वॉइस पहचान अस्थायी रूप से अनुपलब्ध है।",
  "warning.body": "नीचे अपना प्रश्न लिखें — बाकी सब कुछ ठीक काम कर रहा है।",

  "error.micDenied": "माइक्रोफ़ोन एक्सेस अस्वीकृत। कृपया माइक्रोफ़ोन एक्सेस की अनुमति दें।",
  "error.connection": "कनेक्शन त्रुटि। कृपया पुनः प्रयास करें।",
  "error.connectionLost": "कई प्रयासों के बाद कनेक्शन टूट गया। कृपया पुनः प्रयास करें।",
  "error.generic": "कुछ गलत हो गया। कृपया पुनः प्रयास करें।",
};

export default hi;
