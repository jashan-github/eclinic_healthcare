import {
  useConfirmJoinSuccess,
  useLeaveChannel,
  useReportJoinFailure,
  useWaitingRoomStatus,
} from "@/hooks/use-video-call";
import type {
  IAgoraRTCClient,
  IAgoraRTCRemoteUser,
  ICameraVideoTrack,
  IMicrophoneAudioTrack,
} from "agora-rtc-sdk-ng";
import AgoraRTC from "agora-rtc-sdk-ng";
import { useEffect, useRef, useState } from "react";
import { toast } from "react-toastify";
import { useAuth } from "@/context/auth/auth-context-utils";
import {
  Users as UsersIcon,
  VideoCamera as VideoCameraIcon,
  VideoCameraSlash as VideoCameraSlashIcon,
  Microphone as MicrophoneIcon,
  MicrophoneSlash as MicrophoneSlashIcon,
  PhoneDisconnect as PhoneDisconnectIcon,
  X as CloseIcon,
} from "@phosphor-icons/react";

interface AgoraWebinarRoomProps {
  sessionId: string;
  initialJoinData?: any;
  onLeave: () => void;
}

// Audio Level Indicator Component
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

  // Show animated bars based on audio level
  const bars = [0.3, 0.6, 1, 0.6, 0.3]; // Base heights for 5 bars

  return (
    <div className="flex items-end gap-0.5 h-3.5">
      {bars.map((baseHeight, i) => {
        const height =
          level > 0.1 ? Math.min(baseHeight * level * 100, 100) : 20;
        return (
          <div
            key={i}
            className="w-[3px] bg-green-400 rounded-full transition-all duration-75"
            style={{
              height: `${Math.max(height, 20)}%`,
              opacity: level > 0.1 ? 1 : 0.5,
            }}
          />
        );
      })}
    </div>
  );
};

const AgoraVideoCallRoom = ({
  sessionId,
  initialJoinData,
  onLeave,
}: AgoraWebinarRoomProps) => {
  const { user } = useAuth();
  const userId = user?.id || "";
  const userName = user?.name || user?.first_name || "User";
  const isHost = user?.role === "doctor";

  const [localAudioTrack, setLocalAudioTrack] =
    useState<IMicrophoneAudioTrack | null>(null);
  const [localVideoTrack, setLocalVideoTrack] =
    useState<ICameraVideoTrack | null>(null);
  const [remoteUsers, setRemoteUsers] = useState<IAgoraRTCRemoteUser[]>([]);
  const [participantNames, setParticipantNames] = useState<
    Record<string, string>
  >({});
  const [remoteVideoEnabled, setRemoteVideoEnabled] = useState<
    Record<string, boolean>
  >({});
  const [remoteAudioEnabled, setRemoteAudioEnabled] = useState<
    Record<string, boolean>
  >({});
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [isVideoMuted, setIsVideoMuted] = useState(false);
  const [showParticipants, setShowParticipants] = useState(false);
  const [watchdogExpiry, setWatchdogExpiry] = useState<string | null>(null);
  const [channelName, setChannelName] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [appId, setAppId] = useState<string | null>(null);
  const [isWaitingRoom, setIsWaitingRoom] = useState(
    !initialJoinData?.both_ready,
  );

  // Audio level state
  const [localAudioLevel, setLocalAudioLevel] = useState(0);
  const [remoteAudioLevels, setRemoteAudioLevels] = useState<
    Record<string, number>
  >({});
  const audioLevelIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const localVideoRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<IAgoraRTCClient | null>(null);
  const hasJoinedRef = useRef(false);
  const hasReportedFailureRef = useRef(false);

  const confirmJoinSuccess = useConfirmJoinSuccess();
  const reportJoinFailure = useReportJoinFailure();
  const leaveChannelMutation = useLeaveChannel();

  // Audio level monitoring
  useEffect(() => {
    if (!localAudioTrack || isAudioMuted) {
      setLocalAudioLevel(0);
      return;
    }

    audioLevelIntervalRef.current = setInterval(() => {
      // Use type assertion as getVolumeLevel exists at runtime
      const level = (localAudioTrack as any).getVolumeLevel?.() ?? 0;
      setLocalAudioLevel(level);
    }, 100);

    return () => {
      if (audioLevelIntervalRef.current) {
        clearInterval(audioLevelIntervalRef.current);
      }
    };
  }, [localAudioTrack, isAudioMuted]);

  // Monitor remote audio levels
  useEffect(() => {
    const interval = setInterval(() => {
      const levels: Record<string, number> = {};
      remoteUsers.forEach((user) => {
        if (user.audioTrack && remoteAudioEnabled[user.uid]) {
          // Use type assertion as getVolumeLevel exists at runtime
          levels[user.uid] = (user.audioTrack as any).getVolumeLevel?.() ?? 0;
        } else {
          levels[user.uid] = 0;
        }
      });
      setRemoteAudioLevels(levels);
    }, 100);

    return () => clearInterval(interval);
  }, [remoteUsers, remoteAudioEnabled]);

  useEffect(() => {
    if (!initialJoinData) return;

    const {
      token,
      channel_name,
      app_id,
      both_ready,
      watchdog_expires_at,
      waiting_room,
    } = initialJoinData;

    if (app_id) {
      setAppId(app_id);
    }

    if (watchdog_expires_at) {
      setWatchdogExpiry(watchdog_expires_at);
    }

    if (both_ready && token && channel_name) {
      setToken(token);
      setChannelName(channel_name);
      setIsWaitingRoom(false);
      toast.success("Connecting...");
    } else if (waiting_room) {
      setChannelName(channel_name);
      setIsWaitingRoom(true);
    }
  }, [initialJoinData, sessionId]);

  const { data: waitingRoomData } = useWaitingRoomStatus(
    sessionId,
    isWaitingRoom && !token,
  );

  /* -------------------- AGORA CLIENT INIT -------------------- */
  useEffect(() => {
    // RTC mode for two-way video call
    clientRef.current = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
    return () => {
      clientRef.current?.leave();
      clientRef.current = null;
    };
  }, []);

  /* -------------------- WAITING ROOM (TOKEN SOURCE) -------------------- */
  useEffect(() => {
    if (!waitingRoomData?.data) return;
    const { watchdog_expires_at, both_ready } = waitingRoomData.data;

    if (both_ready && watchdog_expires_at) {
      setWatchdogExpiry(watchdog_expires_at);

      const expiryTime = new Date(watchdog_expires_at).getTime();
      const now = Date.now();
      const timeRemaining = expiryTime - now;

      if (timeRemaining > 0) {
        const timer = setTimeout(() => {
          if (!hasJoinedRef.current) {
            toast.error("Join timeout - please try again");
            handleLeave();
          }
        }, timeRemaining);

        return () => clearTimeout(timer);
      }
    }
  }, [waitingRoomData]);

  useEffect(() => {
    if (!waitingRoomData?.data) return;
    if (token) return;

    const {
      waiting_room,
      token: newToken,
      channel_name,
      app_id,
      both_ready,
    } = waitingRoomData.data;

    if (app_id && !appId) {
      setAppId(app_id);
    }

    if (
      waitingRoomData.data.status === "join_failed" ||
      waitingRoomData.data.status === "JOIN_FAILED"
    ) {
      toast.error("Session failed - please try again");
      return;
    }

    if (both_ready && !waiting_room && !newToken) {
      toast.error("Connection error - no token received");
      return;
    }

    if (both_ready && !waiting_room && newToken && channel_name) {
      setToken(newToken);
      setChannelName(channel_name);
      setIsWaitingRoom(false);
      toast.success("Connecting...");
    }
  }, [waitingRoomData, token, sessionId, appId]);

  /* -------------------- AGORA JOIN -------------------- */
  useEffect(() => {
    const client = clientRef.current;
    if (!client) return;
    if (!token || !channelName || isWaitingRoom) return;
    if (!appId) {
      toast.error("Missing App ID - cannot connect");
      return;
    }
    if (hasJoinedRef.current) return;
    if (hasReportedFailureRef.current) return;

    const init = async () => {
      try {
        // Extract actual Agora token from wrapped payload
        let agoraToken = token;
        let otherParticipantName: string | null = null;
        try {
          const decoded = JSON.parse(atob(token!));
          console.log("[Agora] Decoded wrapper:", decoded);
          console.log(
            "[Agora] Inner token starts with:",
            decoded.token?.substring(0, 10),
          );
          if (decoded.token) {
            agoraToken = decoded.token;
          }
          // Extract other participant's name if available
          if (decoded.other_participant_name) {
            otherParticipantName = decoded.other_participant_name;
          }
        } catch {
          // Token is not wrapped, use as-is
        }

        // Set up event listeners BEFORE joining to not miss any events
        const handleUserPublished = async (
          user: IAgoraRTCRemoteUser,
          mediaType: "video" | "audio",
        ) => {
          await client.subscribe(user, mediaType);
          if (mediaType === "video") {
            setRemoteUsers((prev) => {
              const exists = prev.some((u) => u.uid === user.uid);
              if (exists) {
                return prev.map((u) => (u.uid === user.uid ? user : u));
              }
              return [...prev, user];
            });
            // Set participant name and video state
            const displayName =
              otherParticipantName || (isHost ? "Patient" : "Doctor");
            setParticipantNames((prev) => ({
              ...prev,
              [user.uid]: displayName,
            }));
            setRemoteVideoEnabled((prev) => ({
              ...prev,
              [user.uid]: true,
            }));
          }
          if (mediaType === "audio") {
            user.audioTrack?.play();
            setRemoteAudioEnabled((prev) => ({
              ...prev,
              [user.uid]: true,
            }));
          }
        };

        const handleUserUnpublished = (
          user: IAgoraRTCRemoteUser,
          mediaType: "video" | "audio",
        ) => {
          if (mediaType === "video") {
            setRemoteVideoEnabled((prev) => ({
              ...prev,
              [user.uid]: false,
            }));
          }
          if (mediaType === "audio") {
            setRemoteAudioEnabled((prev) => ({
              ...prev,
              [user.uid]: false,
            }));
          }
        };

        const handleUserJoined = (user: IAgoraRTCRemoteUser) => {
          // Add user to list when they join (before they publish)
          setRemoteUsers((prev) => {
            const exists = prev.some((u) => u.uid === user.uid);
            if (exists) return prev;
            return [...prev, user];
          });
          const displayName =
            otherParticipantName || (isHost ? "Patient" : "Doctor");
          setParticipantNames((prev) => ({
            ...prev,
            [user.uid]: displayName,
          }));
        };

        const handleUserLeft = (user: IAgoraRTCRemoteUser) => {
          setRemoteUsers((prev) => prev.filter((u) => u.uid !== user.uid));
          setParticipantNames((prev) => {
            const newNames = { ...prev };
            delete newNames[user.uid];
            return newNames;
          });
          setRemoteVideoEnabled((prev) => {
            const newState = { ...prev };
            delete newState[user.uid];
            return newState;
          });
          setRemoteAudioEnabled((prev) => {
            const newState = { ...prev };
            delete newState[user.uid];
            return newState;
          });
        };

        client.on("user-joined", handleUserJoined);
        client.on("user-published", handleUserPublished);
        client.on("user-unpublished", handleUserUnpublished);
        client.on("user-left", handleUserLeft);

        console.log(
          "[Agora] Final token starts with:",
          agoraToken?.substring(0, 10),
        );
        await client.join(appId, channelName, agoraToken, userId);
        hasJoinedRef.current = true;

        await confirmJoinSuccess.mutateAsync(sessionId);

        // Both host and participants publish their audio/video in RTC mode
        const [audio, video] = await Promise.all([
          AgoraRTC.createMicrophoneAudioTrack(),
          AgoraRTC.createCameraVideoTrack(),
        ]);
        setLocalAudioTrack(audio);
        setLocalVideoTrack(video);
        video.play(localVideoRef.current!);
        await client.publish([audio, video]);

        // Check for already-joined remote users (in case they joined before us)
        // Use type assertion since remoteUsers exists at runtime but may not be in type defs
        const existingUsers = (client as any).remoteUsers as
          | IAgoraRTCRemoteUser[]
          | undefined;
        if (existingUsers && existingUsers.length > 0) {
          for (const remoteUser of existingUsers) {
            // Add user to list
            setRemoteUsers((prev) => {
              const exists = prev.some((u) => u.uid === remoteUser.uid);
              if (exists) return prev;
              return [...prev, remoteUser];
            });
            const displayName =
              otherParticipantName || (isHost ? "Patient" : "Doctor");
            setParticipantNames((prev) => ({
              ...prev,
              [remoteUser.uid]: displayName,
            }));

            // Subscribe to video if available
            if (remoteUser.videoTrack) {
              await client.subscribe(remoteUser, "video");
              setRemoteVideoEnabled((prev) => ({
                ...prev,
                [remoteUser.uid]: true,
              }));
            }
            // Subscribe to audio if available
            if (remoteUser.audioTrack) {
              await client.subscribe(remoteUser, "audio");
              remoteUser.audioTrack?.play();
              setRemoteAudioEnabled((prev) => ({
                ...prev,
                [remoteUser.uid]: true,
              }));
            }
          }
        }
      } catch (err) {
        console.error("[Agora] Join failed:", err);
        hasReportedFailureRef.current = true;
        reportJoinFailure.mutateAsync(sessionId);
        toast.error("Failed to join session");
      }
    };

    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, channelName, isWaitingRoom, appId, userId, isHost, sessionId]);

  /* -------------------- CONTROLS -------------------- */
  const toggleAudio = async () => {
    if (localAudioTrack) {
      await localAudioTrack.setEnabled(isAudioMuted);
      setIsAudioMuted(!isAudioMuted);
    }
  };

  const toggleVideo = async () => {
    if (localVideoTrack) {
      await localVideoTrack.setEnabled(isVideoMuted);
      setIsVideoMuted(!isVideoMuted);
    }
  };

  const handleLeave = async () => {
    try {
      // Notify backend that user is leaving the channel
      if (hasJoinedRef.current) {
        try {
          await leaveChannelMutation.mutateAsync(sessionId);
        } catch (e) {
          console.error("Failed to notify leave-channel:", e);
        }
      }

      await clientRef.current?.leave();
      localAudioTrack?.close();
      localVideoTrack?.close();
    } finally {
      hasJoinedRef.current = false;
      hasReportedFailureRef.current = false;
      onLeave();
    }
  };

  /* -------------------- WAITING ROOM UI -------------------- */
  if (isWaitingRoom) {
    return (
      <div className="fixed inset-0 bg-gray-900 z-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-white mx-auto mb-6" />
          <h2 className="text-white text-2xl font-semibold mb-2">
            Waiting Room
          </h2>
          <p className="text-gray-400">
            {isHost
              ? "Waiting for patient to join..."
              : "Waiting for doctor to join..."}
          </p>

          {watchdogExpiry && (
            <p className="text-yellow-400 text-sm mt-2">
              Join window expires at:{" "}
              {new Date(watchdogExpiry).toLocaleTimeString()}
            </p>
          )}

          <button
            onClick={onLeave}
            className="mt-8 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg cursor-pointer"
          >
            {isHost ? "Cancel Call" : "Leave Waiting Room"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-900 z-50 flex flex-col">
      {/* Top Bar */}
      <div className="bg-gray-800/90 backdrop-blur-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-white font-medium text-sm">Video Call</span>
          </div>
          <span className="text-gray-400 text-xs hidden sm:inline">
            {remoteUsers.length + 1} participant
            {remoteUsers.length + 1 !== 1 ? "s" : ""}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowParticipants(!showParticipants)}
            className={`p-2 rounded-lg text-white transition cursor-pointer ${
              showParticipants ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"
            }`}
          >
            <UsersIcon size={20} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Video Area */}
        <div
          className={`flex-1 flex items-stretch p-2 md:p-4 relative overflow-hidden transition-all ${showParticipants ? "mr-0" : ""}`}
        >
          {/* Normal Video Call Layout */}
          {(() => {
            const totalParticipants = 1 + remoteUsers.length;

            const getGridClasses = () => {
              if (totalParticipants === 1) {
                return "grid-cols-1";
              } else if (totalParticipants === 2) {
                return "grid-cols-1 md:grid-cols-2";
              } else if (totalParticipants === 3) {
                return "grid-cols-2 grid-rows-2";
              } else if (totalParticipants === 4) {
                return "grid-cols-2 grid-rows-2";
              } else {
                return "grid-cols-2 md:grid-cols-3";
              }
            };

            const getItemClasses = (index: number) => {
              if (totalParticipants === 3 && index === 2) {
                return "col-span-2 md:col-span-1 md:col-start-2 md:row-start-1 md:row-span-2";
              }
              return "";
            };

            return (
              <div
                className={`grid ${getGridClasses()} gap-2 md:gap-3 w-full h-full`}
              >
                {/* Local Video */}
                <div
                  className={`relative bg-gray-800 rounded-xl overflow-hidden ${getItemClasses(0)}`}
                >
                  <div
                    ref={localVideoRef}
                    className={`w-full h-full ${isVideoMuted ? "hidden" : ""}`}
                    style={{ minHeight: 0 }}
                  ></div>
                  {isVideoMuted && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-700">
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-gray-600 flex items-center justify-center">
                          <span className="text-3xl md:text-4xl text-white font-semibold">
                            {userName.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="text-gray-400 text-sm">
                          Camera off
                        </span>
                      </div>
                    </div>
                  )}
                  {/* Name badge with audio level indicator */}
                  <div className="absolute bottom-3 left-3 flex items-center gap-2">
                    <div className="bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-lg text-white text-sm font-medium flex items-center gap-2">
                      <AudioLevelIndicator
                        level={localAudioLevel}
                        isMuted={isAudioMuted}
                      />
                      {userName} (You)
                    </div>
                  </div>
                </div>

                {/* Remote Users */}
                {remoteUsers.map((user, index) => {
                  const hasVideo = remoteVideoEnabled[user.uid];
                  const hasAudio = remoteAudioEnabled[user.uid];
                  const displayName =
                    participantNames[user.uid] ||
                    (isHost ? "Patient" : "Doctor");
                  const audioLevel = remoteAudioLevels[user.uid] || 0;

                  return (
                    <div
                      key={user.uid}
                      className={`relative bg-gray-800 rounded-xl overflow-hidden ${getItemClasses(index + 1)}`}
                    >
                      {/* Video container */}
                      <div
                        ref={(ref) => {
                          if (ref && user.videoTrack && hasVideo) {
                            user.videoTrack.play(ref);
                          }
                        }}
                        className={`w-full h-full ${!hasVideo ? "hidden" : ""}`}
                        style={{ minHeight: 0 }}
                      ></div>

                      {/* Placeholder when video is off */}
                      {!hasVideo && (
                        <div className="absolute inset-0 flex items-center justify-center bg-gray-700">
                          <div className="flex flex-col items-center gap-2">
                            <div className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-gray-600 flex items-center justify-center">
                              <span className="text-3xl md:text-4xl text-white font-semibold">
                                {displayName.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <span className="text-gray-400 text-sm">
                              Camera off
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Name badge with audio level indicator */}
                      <div className="absolute bottom-3 left-3 flex items-center gap-2">
                        <div className="bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-lg text-white text-sm font-medium flex items-center gap-2">
                          <AudioLevelIndicator
                            level={audioLevel}
                            isMuted={!hasAudio}
                          />
                          {displayName}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })()}

          {/* No Other Participants Overlay */}
          {remoteUsers.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="bg-black/40 backdrop-blur-sm px-6 py-4 rounded-xl text-center">
                <p className="text-white text-lg font-medium">
                  Waiting for {isHost ? "patient" : "doctor"} to join...
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        {showParticipants && (
          <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col">
            {/* Sidebar Header */}
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-white font-medium">Participants</h3>
              <button
                onClick={() => setShowParticipants(false)}
                className="p-1 text-gray-400 hover:text-white transition cursor-pointer"
              >
                <CloseIcon size={20} />
              </button>
            </div>

            {/* Participants List */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-3">
                {/* Local user */}
                <div className="flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg">
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
                    <span className="text-white font-medium">
                      {userName.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1">
                    <p className="text-white text-sm font-medium">
                      {userName} (You)
                    </p>
                    <p className="text-gray-400 text-xs">
                      {isHost ? "Host" : "Participant"}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <AudioLevelIndicator
                      level={localAudioLevel}
                      isMuted={isAudioMuted}
                    />
                    {isVideoMuted ? (
                      <VideoCameraSlashIcon
                        size={16}
                        className="text-red-400"
                      />
                    ) : (
                      <VideoCameraIcon size={16} className="text-green-400" />
                    )}
                  </div>
                </div>

                {/* Remote users */}
                {remoteUsers.map((user) => {
                  const displayName =
                    participantNames[user.uid] ||
                    (isHost ? "Patient" : "Doctor");
                  const hasVideo = remoteVideoEnabled[user.uid];
                  const hasAudio = remoteAudioEnabled[user.uid];
                  const audioLevel = remoteAudioLevels[user.uid] || 0;

                  return (
                    <div
                      key={user.uid}
                      className="flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg"
                    >
                      <div className="w-10 h-10 rounded-full bg-green-600 flex items-center justify-center">
                        <span className="text-white font-medium">
                          {displayName.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="text-white text-sm font-medium">
                          {displayName}
                        </p>
                        <p className="text-gray-400 text-xs">
                          {isHost ? "Participant" : "Host"}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <AudioLevelIndicator
                          level={audioLevel}
                          isMuted={!hasAudio}
                        />
                        {!hasVideo ? (
                          <VideoCameraSlashIcon
                            size={16}
                            className="text-red-400"
                          />
                        ) : (
                          <VideoCameraIcon
                            size={16}
                            className="text-green-400"
                          />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Controls Bar (Bottom) */}
      <div className="bg-gray-800 p-4 flex items-center justify-center gap-4">
        {/* Audio Toggle */}
        <button
          onClick={toggleAudio}
          className={`p-4 rounded-full transition cursor-pointer ${
            isAudioMuted
              ? "bg-red-600 hover:bg-red-700"
              : "bg-gray-700 hover:bg-gray-600"
          }`}
        >
          {isAudioMuted ? (
            <MicrophoneSlashIcon size={24} className="text-white" />
          ) : (
            <MicrophoneIcon size={24} className="text-white" />
          )}
        </button>

        {/* Video Toggle */}
        <button
          onClick={toggleVideo}
          className={`p-4 rounded-full transition cursor-pointer ${
            isVideoMuted
              ? "bg-red-600 hover:bg-red-700"
              : "bg-gray-700 hover:bg-gray-600"
          }`}
        >
          {isVideoMuted ? (
            <VideoCameraSlashIcon size={24} className="text-white" />
          ) : (
            <VideoCameraIcon size={24} className="text-white" />
          )}
        </button>

        {/* Leave */}
        <button
          onClick={handleLeave}
          className="p-4 bg-red-600 hover:bg-red-700 rounded-full transition ml-4 cursor-pointer"
        >
          <PhoneDisconnectIcon size={24} className="text-white" />
        </button>
      </div>
    </div>
  );
};

export default AgoraVideoCallRoom;
