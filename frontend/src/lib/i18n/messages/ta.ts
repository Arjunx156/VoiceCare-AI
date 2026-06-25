/** Tamil (தமிழ்). Machine-assisted draft — review by a native speaker before production. */
import type { Messages } from "./en";

const ta: Messages = {
  "voice.eyebrow.listening": "கேட்கிறேன்",
  "voice.eyebrow.thinking": "யோசிக்கிறேன்",
  "voice.eyebrow.done": "முடிந்தது",
  "voice.eyebrow.idle": "குரல் ஆதரவு",

  "voice.headline.listening": "நான் கேட்கிறேன்…",
  "voice.headline.thinking": "வேலை செய்கிறது…",
  "voice.headline.done": "நான் கண்டறிந்தது இதோ",
  "voice.headline.idle": "உங்கள் பிரச்சினையைச் சொல்லுங்கள்",

  "footer.startRecording": "பதிவைத் தொடங்கு",
  "footer.stopRecording": "பதிவை நிறுத்து",
  "footer.send": "அனுப்பு",
  "footer.placeholder": "எந்த மொழியிலும் உங்கள் கேள்வியைத் தட்டச்சு செய்யுங்கள்…",
  "footer.switchToVoice": "குரலுக்கு மாறு",
  "footer.switchToText": "உரைக்கு மாறு",

  "status.processing": "செயலாக்கப்படுகிறது",
  "status.complete": "முடிந்தது",
  "status.stage1": "ஒலி பெறப்படுகிறது",
  "status.stage2": "நோக்கம் புரிந்துகொள்கிறது",
  "status.stage3": "ஆர்டரைப் பார்க்கிறது",
  "status.stage4": "கொள்கையைப் பெறுகிறது",
  "status.stage5": "தீர்வை நிர்ணயிக்கிறது",
  "status.stage6": "மேலெழுப்பலைச் சரிபார்க்கிறது",
  "status.stage7": "பதிலை உருவாக்குகிறது",
  "status.stage8": "பேச்சாக மாற்றுகிறது",
  "status.stage9": "டிக்கெட் உருவாக்குகிறது",

  "response.escalated": "மேலெழுப்பப்பட்டது",
  "response.resolved": "தீர்க்கப்பட்டது",
  "response.ticket": "டிக்கெட்",
  "response.confidence": "நம்பிக்கை",

  "warning.title": "குரல் அங்கீகாரம் தற்காலிகமாக கிடைக்கவில்லை.",
  "warning.body": "கீழே உங்கள் கேள்வியைத் தட்டச்சு செய்யுங்கள் — மற்ற அனைத்தும் சரியாக வேலை செய்கிறது.",

  "error.micDenied": "மைக்ரோஃபோன் அணுகல் மறுக்கப்பட்டது. தயவுசெய்து மைக்ரோஃபோன் அணுகலை அனுமதிக்கவும்.",
  "error.connection": "இணைப்பு பிழை. மீண்டும் முயற்சிக்கவும்.",
  "error.connectionLost": "பல முயற்சிகளுக்குப் பிறகு இணைப்பு துண்டிக்கப்பட்டது. மீண்டும் முயற்சிக்கவும்.",
  "error.generic": "ஏதோ தவறு நடந்தது. மீண்டும் முயற்சிக்கவும்.",
};

export default ta;
