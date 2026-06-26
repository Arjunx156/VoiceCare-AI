/** Bengali (বাংলা). Machine-assisted draft — review by a native speaker before production. */
import type { Messages } from "./en";

const bn: Messages = {
  "voice.eyebrow.listening": "শুনছি",
  "voice.eyebrow.thinking": "ভাবছি",
  "voice.eyebrow.done": "সম্পন্ন",
  "voice.eyebrow.idle": "ভয়েস সহায়তা",

  "voice.headline.listening": "আমি শুনছি…",
  "voice.headline.thinking": "কাজ চলছে…",
  "voice.headline.done": "এই নিন আমি যা পেলাম",
  "voice.headline.idle": "আপনার সমস্যা বলুন",

  "footer.startRecording": "রেকর্ডিং শুরু করুন",
  "footer.stopRecording": "রেকর্ডিং বন্ধ করুন",
  "footer.send": "পাঠান",
  "footer.placeholder": "যেকোনো ভাষায় আপনার প্রশ্ন টাইপ করুন…",
  "footer.switchToVoice": "ভয়েসে যান",
  "footer.switchToText": "টেক্সটে যান",
  "footer.newConversation": "নতুন কথোপকথন",

  "status.processing": "প্রক্রিয়াকরণ হচ্ছে",
  "status.complete": "সম্পন্ন",
  "status.stage1": "অডিও গ্রহণ করা হচ্ছে",
  "status.stage2": "উদ্দেশ্য বোঝা হচ্ছে",
  "status.stage3": "অর্ডার দেখা হচ্ছে",
  "status.stage4": "নীতি আনা হচ্ছে",
  "status.stage5": "সমাধান নির্ধারণ করা হচ্ছে",
  "status.stage6": "এস্কালেশন পরীক্ষা করা হচ্ছে",
  "status.stage7": "উত্তর তৈরি করা হচ্ছে",
  "status.stage8": "বাক্যে রূপান্তর করা হচ্ছে",
  "status.stage9": "টিকিট তৈরি করা হচ্ছে",

  "response.escalated": "এস্কালেট করা হয়েছে",
  "response.resolved": "সমাধান হয়েছে",
  "response.ticket": "টিকিট",
  "response.confidence": "আত্মবিশ্বাস",

  "warning.title": "ভয়েস স্বীকৃতি সাময়িকভাবে অনুপলব্ধ।",
  "warning.body": "নিচে আপনার প্রশ্ন টাইপ করুন — বাকি সবকিছু ঠিকঠাক কাজ করছে।",

  "error.micDenied": "মাইক্রোফোন অ্যাক্সেস অস্বীকৃত। অনুগ্রহ করে মাইক্রোফোন অ্যাক্সেস অনুমতি দিন।",
  "error.connection": "সংযোগ ত্রুটি। অনুগ্রহ করে আবার চেষ্টা করুন।",
  "error.connectionLost": "একাধিক চেষ্টার পরে সংযোগ বিচ্ছিন্ন হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
  "error.generic": "কিছু একটা ভুল হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
};

export default bn;
