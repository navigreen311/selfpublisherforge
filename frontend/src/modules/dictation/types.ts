export interface DictationSettings {
  language: string;
  microphoneDeviceId: string;
  autoRefine: boolean;
  voiceCommandsEnabled: boolean;
}

export interface DictationCommand {
  id: string;
  phrase: string;
  action: string;
  active: boolean;
  builtIn: boolean;
}

export interface DiffSegment {
  type: "unchanged" | "added" | "removed" | "changed";
  rawText: string;
  refinedText: string;
}

export interface LowConfidenceWord {
  word: string;
  confidence: number;
  index: number;
}

export interface VoiceCommandEvent {
  command: string;
  action: string;
}
