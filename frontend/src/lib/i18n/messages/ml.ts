/** Malayalam (മലയാളം). Machine-assisted draft — review by a native speaker before production. */
import type { Messages } from "./en";

const ml: Messages = {
  "voice.eyebrow.listening": "കേൾക്കുന്നു",
  "voice.eyebrow.thinking": "ചിന്തിക്കുന്നു",
  "voice.eyebrow.done": "പൂർത്തിയായി",
  "voice.eyebrow.idle": "വോയിസ് സഹായം",

  "voice.headline.listening": "ഞാൻ കേൾക്കുന്നു…",
  "voice.headline.thinking": "പ്രവർത്തിക്കുന്നു…",
  "voice.headline.done": "ഇതാ ഞാൻ കണ്ടെത്തിയത്",
  "voice.headline.idle": "നിങ്ങളുടെ പ്രശ്നം പറയൂ",

  "footer.startRecording": "റെക്കോർഡിംഗ് ആരംഭിക്കുക",
  "footer.stopRecording": "റെക്കോർഡിംഗ് നിർത്തുക",
  "footer.send": "അയയ്ക്കുക",
  "footer.placeholder": "ഏത് ഭാഷയിലും നിങ്ങളുടെ ചോദ്യം ടൈപ്പ് ചെയ്യൂ…",
  "footer.switchToVoice": "വോയിസിലേക്ക് മാറുക",
  "footer.switchToText": "ടെക്സ്റ്റിലേക്ക് മാറുക",

  "status.processing": "പ്രോസസ്സ് ചെയ്യുന്നു",
  "status.complete": "പൂർത്തിയായി",
  "status.stage1": "ഓഡിയോ സ്വീകരിക്കുന്നു",
  "status.stage2": "ഉദ്ദേശ്യം മനസ്സിലാക്കുന്നു",
  "status.stage3": "ഓർഡർ പരിശോധിക്കുന്നു",
  "status.stage4": "നയം എടുക്കുന്നു",
  "status.stage5": "പരിഹാരം നിർണ്ണയിക്കുന്നു",
  "status.stage6": "എസ്കലേഷൻ പരിശോധിക്കുന്നു",
  "status.stage7": "മറുപടി തയ്യാറാക്കുന്നു",
  "status.stage8": "സംസാരമാക്കി മാറ്റുന്നു",
  "status.stage9": "ടിക്കറ്റ് സൃഷ്ടിക്കുന്നു",

  "response.escalated": "എസ്കലേറ്റ് ചെയ്തു",
  "response.resolved": "പരിഹരിച്ചു",
  "response.ticket": "ടിക്കറ്റ്",
  "response.confidence": "ആത്മവിശ്വാസം",

  "warning.title": "വോയിസ് തിരിച്ചറിയൽ താൽക്കാലികമായി ലഭ്യമല്ല.",
  "warning.body": "താഴെ നിങ്ങളുടെ ചോദ്യം ടൈപ്പ് ചെയ്യൂ — മറ്റെല്ലാം നന്നായി പ്രവർത്തിക്കുന്നു.",

  "error.micDenied": "മൈക്രോഫോൺ ആക്സസ് നിഷേധിച്ചു. ദയവായി മൈക്രോഫോൺ ആക്സസ് അനുവദിക്കൂ.",
  "error.connection": "കണക്ഷൻ പിശക്. ദയവായി വീണ്ടും ശ്രമിക്കൂ.",
  "error.connectionLost": "നിരവധി ശ്രമങ്ങൾക്ക് ശേഷം കണക്ഷൻ നഷ്ടപ്പെട്ടു. ദയവായി വീണ്ടും ശ്രമിക്കൂ.",
  "error.generic": "എന്തോ കുഴപ്പം സംഭവിച്ചു. ദയവായി വീണ്ടും ശ്രമിക്കൂ.",
};

export default ml;
