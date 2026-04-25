import {
  HandPalmIcon,
  UserMinusIcon,
  CheckIcon,
  SpeakerSlashIcon,
  MicrophoneIcon,
  MicrophoneSlashIcon,
  XIcon,
} from "@phosphor-icons/react";
import type { Participant } from "@/hooks/use-webinar-rtm";

const AudioLevelIndicator = ({
  level,
  isMuted,
}: {
  level: number;
  isMuted: boolean;
}) => {
  if (isMuted) {
    return <MicrophoneSlashIcon size={14} className="text-red-400" />;
  }

  if (level <= 0.1) {
    return <MicrophoneIcon size={14} className="text-green-400" />;
  }

  const bars = [0.3, 0.6, 1, 0.6, 0.3];

  return (
    <div className="flex items-end gap-0.5 h-3.5">
      {bars.map((baseHeight, i) => {
        const height = Math.min(baseHeight * level * 100, 100);
        return (
          <div
            key={i}
            className="w-[3px] bg-green-400 rounded-full transition-all duration-75"
            style={{ height: `${Math.max(height, 20)}%` }}
          />
        );
      })}
    </div>
  );
};

interface WebinarParticipantsPanelProps {
  participants: Participant[];
  currentUserId: string;
  isHost: boolean;
  mutedUserIds: Set<string>;
  localAudioLevel: number;
  remoteAudioLevels: Record<string, number>;
  onKickUser: (userId: string) => void;
  onMuteAll: () => void;
  onDismissHand: (userId: string) => void;
  onClose: () => void;
}

const WebinarParticipantsPanel = ({
  participants,
  currentUserId,
  isHost,
  mutedUserIds,
  localAudioLevel,
  remoteAudioLevels,
  onKickUser,
  onMuteAll,
  onDismissHand,
  onClose,
}: WebinarParticipantsPanelProps) => {
  return (
    <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <span className="text-white font-semibold">
          Participants ({participants.length})
        </span>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition"
        >
          <XIcon size={18} />
        </button>
      </div>

      {/* Host: Mute All button */}
      {isHost && (
        <div className="p-3 border-b border-gray-700">
          <button
            onClick={onMuteAll}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition active:scale-95"
          >
            <SpeakerSlashIcon size={18} />
            Mute All Audience
          </button>
        </div>
      )}

      {/* Participant list */}
      <div className="flex-1 overflow-y-auto">
        {participants.map((p) => {
          const isSelf = p.userId === currentUserId;
          const audioLevel = isSelf
            ? localAudioLevel
            : (remoteAudioLevels[p.userId] ?? 0);
          const isMuted = mutedUserIds.has(p.userId);

          return (
            <div
              key={p.userId}
              className="flex items-center gap-3 px-3 py-2 hover:bg-gray-750 hover:bg-opacity-50"
            >
              {/* Avatar */}
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium shrink-0">
                {p.userName.charAt(0).toUpperCase()}
              </div>

              {/* Name */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-white text-sm truncate">
                    {p.userName}
                  </span>
                  {isSelf && (
                    <span className="text-gray-400 text-xs">(You)</span>
                  )}
                  {p.isHost && (
                    <span className="text-yellow-400 text-xs">(Host)</span>
                  )}
                </div>
              </div>

              {/* Audio level indicator */}
              <div className="shrink-0">
                <AudioLevelIndicator level={audioLevel} isMuted={isMuted} />
              </div>

              {/* Hand raised indicator */}
              {p.handRaised && (
                <HandPalmIcon
                  size={18}
                  weight="fill"
                  className="text-yellow-400 shrink-0"
                />
              )}

              {/* Host controls (not for self) */}
              {isHost && !isSelf && (
                <div className="flex items-center gap-1 shrink-0">
                  {p.handRaised && (
                    <button
                      onClick={() => onDismissHand(p.userId)}
                      className="p-1 hover:bg-green-600 rounded text-green-400 hover:text-white transition"
                      title="Dismiss hand"
                    >
                      <CheckIcon size={16} />
                    </button>
                  )}
                  <button
                    onClick={() => onKickUser(p.userId)}
                    className="p-1 hover:bg-red-600 rounded text-red-400 hover:text-white transition"
                    title="Remove participant"
                  >
                    <UserMinusIcon size={16} />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default WebinarParticipantsPanel;
