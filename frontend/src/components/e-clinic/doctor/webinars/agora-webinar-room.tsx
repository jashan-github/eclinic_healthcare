import { useEffect, useMemo, useRef, useState } from 'react'
import AgoraRTC, {
  type IAgoraRTCClient,
  type IAgoraRTCRemoteUser,
  type ICameraVideoTrack,
  type IMicrophoneAudioTrack
} from 'agora-rtc-sdk-ng'
import {
  MicrophoneSlashIcon,
  MicrophoneIcon,
  VideoCameraSlashIcon,
  VideoCameraIcon,
  MonitorIcon,
  PhoneDisconnectIcon,
  UsersIcon,
  ChatCircleIcon,
  HandPalmIcon
} from '@phosphor-icons/react'
import { toast } from 'react-toastify'
import {
  useAdminGoLiveWebinar,
  useGoLiveWebinar,
  useDoctorJoinWebinar,
  usePatientJoinWebinar,
  useWebinarWaitingRoomPoll,
} from '@/hooks/use-webinar-livestream'
import {
  isWaitingRoom,
  type WebinarLivestreamCredentials,
} from '@/services/webinar-livestream-service'
import { useAuth } from '@/context/auth/auth-context-utils'
import { useWebinarRtm } from '@/hooks/use-webinar-rtm'
import WebinarChatPanel from './webinar-chat-panel'
import WebinarParticipantsPanel from './webinar-participants-panel'

const AudioLevelIndicator = ({
  level,
  isMuted,
}: {
  level: number
  isMuted: boolean
}) => {
  if (isMuted) {
    return <MicrophoneSlashIcon size={14} className="text-red-400" />
  }

  if (level <= 0.1) {
    return <MicrophoneIcon size={14} className="text-green-400" />
  }

  const bars = [0.3, 0.6, 1, 0.6, 0.3]

  return (
    <div className="flex items-end gap-0.5 h-3.5">
      {bars.map((baseHeight, i) => {
        const height = Math.min(baseHeight * level * 100, 100)
        return (
          <div
            key={i}
            className="w-[3px] bg-green-400 rounded-full transition-all duration-75"
            style={{ height: `${Math.max(height, 20)}%` }}
          />
        )
      })}
    </div>
  )
}

interface AgoraWebinarRoomProps {
  webinarId: string
  isHost: boolean
  userRole: 'admin' | 'doctor' | 'patient'
  userName: string
  onLeave: () => void
}

const AgoraWebinarRoom = ({
  webinarId,
  isHost,
  userRole,
  userName,
  onLeave
}: AgoraWebinarRoomProps) => {
  const { user } = useAuth()
  const userId = user?.id || ''

  const [client] = useState<IAgoraRTCClient>(() =>
    AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' })
  )
  const [localAudioTrack, setLocalAudioTrack] = useState<IMicrophoneAudioTrack | null>(null)
  const [localVideoTrack, setLocalVideoTrack] = useState<ICameraVideoTrack | null>(null)
  const [remoteUsers, setRemoteUsers] = useState<IAgoraRTCRemoteUser[]>([])
  const [isAudioMuted, setIsAudioMuted] = useState(false)
  const [isVideoMuted, setIsVideoMuted] = useState(false)
  const [screenTrack, setScreenTrack] = useState<ICameraVideoTrack | null>(null)
  const [isScreenSharing, setIsScreenSharing] = useState(false)
  const [showParticipants, setShowParticipants] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [credentials, setCredentials] = useState<WebinarLivestreamCredentials | null>(null)
  const [inWaitingRoom, setInWaitingRoom] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [isJoined, setIsJoined] = useState(false)

  const localVideoRef = useRef<HTMLDivElement>(null)
  const hasInitRef = useRef(false)
  const audioLevelIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [localAudioLevel, setLocalAudioLevel] = useState(0)
  const [remoteAudioLevels, setRemoteAudioLevels] = useState<Record<string, number>>({})

  // Messaging hook (uses RTC data streams)
  const rtm = useWebinarRtm({
    rtcClient: client,
    userId,
    userName,
    isHost,
    enabled: isJoined,
  })

  // Build display participants from RTM + RTC remote users
  // RTM may fail to connect, so we always include remote RTC users as fallback
  const displayParticipants = useMemo(() => {
    const map = new Map(rtm.participants.map((p) => [p.userId, p]))

    // Ensure self is always present
    if (!map.has(userId)) {
      map.set(userId, { userId, userName, isHost, handRaised: false })
    }

    // Add remote RTC users that RTM didn't discover
    for (const remote of remoteUsers) {
      const uid = String(remote.uid)
      if (!map.has(uid)) {
        map.set(uid, {
          userId: uid,
          userName: isHost ? `Participant` : 'Host',
          isHost: !isHost,
          handRaised: false,
        })
      }
    }

    return Array.from(map.values())
  }, [rtm.participants, remoteUsers, userId, userName, isHost])

  // Build set of muted user IDs from local state + remote users
  const mutedUserIds = useMemo(() => {
    const set = new Set<string>()
    if (isAudioMuted) set.add(userId)
    for (const remote of remoteUsers) {
      if (!(remote as any).hasAudio) {
        set.add(String(remote.uid))
      }
    }
    return set
  }, [isAudioMuted, userId, remoteUsers])

  // Monitor local audio level
  useEffect(() => {
    if (!localAudioTrack || isAudioMuted) {
      setLocalAudioLevel(0)
      return
    }

    audioLevelIntervalRef.current = setInterval(() => {
      const level = (localAudioTrack as any).getVolumeLevel?.() ?? 0
      setLocalAudioLevel(level)
    }, 100)

    return () => {
      if (audioLevelIntervalRef.current) {
        clearInterval(audioLevelIntervalRef.current)
      }
    }
  }, [localAudioTrack, isAudioMuted])

  // Monitor remote audio levels
  useEffect(() => {
    const interval = setInterval(() => {
      const levels: Record<string, number> = {}
      remoteUsers.forEach((user) => {
        if (user.audioTrack) {
          levels[String(user.uid)] = (user.audioTrack as any).getVolumeLevel?.() ?? 0
        } else {
          levels[String(user.uid)] = 0
        }
      })
      setRemoteAudioLevels(levels)
    }, 100)

    return () => clearInterval(interval)
  }, [remoteUsers])

  // Mutations
  const adminGoLive = useAdminGoLiveWebinar()
  const goLive = useGoLiveWebinar()
  const doctorJoin = useDoctorJoinWebinar()
  const patientJoin = usePatientJoinWebinar()

  // Waiting room polling
  const { data: pollData } = useWebinarWaitingRoomPoll(
    webinarId,
    userRole,
    inWaitingRoom
  )

  // Track unread chat messages when panel is closed + show toast notification
  const prevMessageCountRef = useRef(0)
  useEffect(() => {
    const currentCount = rtm.chatMessages.length
    if (!showChat && currentCount > prevMessageCountRef.current) {
      setUnreadCount((prev) => prev + (currentCount - prevMessageCountRef.current))
      // Show toast for the latest message
      const lastMsg = rtm.chatMessages[currentCount - 1]
      if (lastMsg && lastMsg.senderId !== userId) {
        const preview = lastMsg.text.length > 50 ? lastMsg.text.slice(0, 50) + '...' : lastMsg.text
        toast.info(`${lastMsg.senderName}: ${preview}`, { autoClose: 3000 })
      }
    }
    prevMessageCountRef.current = currentCount
  }, [rtm.chatMessages.length, showChat, rtm.chatMessages, userId])

  // Reset unread when chat opens
  useEffect(() => {
    if (showChat) {
      setUnreadCount(0)
    }
  }, [showChat])

  // React to kick
  useEffect(() => {
    if (rtm.isKicked) {
      toast.error('You have been removed from the webinar')
      handleLeave()
    }
  }, [rtm.isKicked])

  // React to force mute — disable own microphone (counter-based so it re-triggers)
  useEffect(() => {
    if (rtm.forceMuteCount > 0 && localAudioTrack) {
      localAudioTrack.setEnabled(false)
      setIsAudioMuted(true)
      toast.info('The host has muted your microphone')
    }
  }, [rtm.forceMuteCount, localAudioTrack])

  // Sidebar toggle helpers — only one open at a time
  const toggleParticipants = () => {
    setShowParticipants((prev) => {
      if (!prev) setShowChat(false)
      return !prev
    })
  }

  const toggleChat = () => {
    setShowChat((prev) => {
      if (!prev) setShowParticipants(false)
      return !prev
    })
  }

  // Step 1: Call the appropriate endpoint on mount
  useEffect(() => {
    if (hasInitRef.current) return
    hasInitRef.current = true

    const init = async () => {
      try {
        if (isHost) {
          const goLiveMutation = userRole === 'admin' ? adminGoLive : goLive
          const creds = await goLiveMutation.mutateAsync(webinarId)
          setCredentials(creds)
        } else {
          const joinMutation = userRole === 'doctor' ? doctorJoin : patientJoin
          const response = await joinMutation.mutateAsync(webinarId)

          if (isWaitingRoom(response)) {
            setInWaitingRoom(true)
            toast.info('Waiting for the host to go live...')
          } else {
            setCredentials(response)
          }
        }
      } catch (error) {
        console.error('Failed to initialize webinar:', error)
        toast.error('Failed to join webinar')
      }
    }

    init()
  }, [])

  // Step 2: Handle waiting room poll results
  useEffect(() => {
    if (!inWaitingRoom || !pollData) return

    if (!isWaitingRoom(pollData)) {
      setCredentials(pollData)
      setInWaitingRoom(false)
      toast.success('Host is live! Connecting...')
    }
  }, [pollData, inWaitingRoom])

  // Step 3: Join Agora channel once credentials are available
  useEffect(() => {
    if (!credentials) return

    const joinChannel = async () => {
      try {
        // Register listeners BEFORE joining so we don't miss events
        // for users already in the channel
        client.on('user-joined', (user) => {
          setRemoteUsers((prev) => {
            if (prev.some((u) => u.uid === user.uid)) return prev
            return [...prev, user]
          })
        })

        client.on('user-published', async (user, mediaType) => {
          await client.subscribe(user, mediaType)

          if (mediaType === 'video') {
            setRemoteUsers((prev) => {
              const exists = prev.some((u) => u.uid === user.uid)
              if (exists) return prev.map((u) => (u.uid === user.uid ? user : u))
              return [...prev, user]
            })
          }

          if (mediaType === 'audio') {
            user.audioTrack?.play()
          }
        })

        client.on('user-unpublished', (user, mediaType) => {
          if (mediaType === 'video') {
            setRemoteUsers((prev) =>
              prev.map((u) => (u.uid === user.uid ? user : u))
            )
          }
        })

        client.on('user-left', (user) => {
          setRemoteUsers((prev) => prev.filter((u) => u.uid !== user.uid))
        })

        await client.join(
          credentials.app_id,
          credentials.channel_name,
          credentials.token,
          userId
        )

        setIsJoined(true)

        // All participants publish audio/video in RTC mode
        try {
          const [audioTrack, videoTrack] = await Promise.all([
            AgoraRTC.createMicrophoneAudioTrack().catch((err) => {
              console.error('Failed to create audio track:', err)
              toast.error('Microphone access denied or unavailable')
              throw err
            }),
            AgoraRTC.createCameraVideoTrack().catch((err) => {
              console.error('Failed to create video track:', err)
              toast.error('Camera access denied or unavailable')
              throw err
            })
          ])

          setLocalAudioTrack(audioTrack)
          setLocalVideoTrack(videoTrack)

          if (localVideoRef.current) {
            videoTrack.play(localVideoRef.current)
          }

          await client.publish([audioTrack, videoTrack])
          toast.success(isHost ? 'You are now live!' : 'Joined webinar successfully!')
        } catch (trackError) {
          console.error('Failed to initialize media tracks:', trackError)
          toast.error('Failed to access camera/microphone. Please check permissions.')
        }
      } catch (error) {
        console.error('Failed to join Agora channel:', error)
        toast.error('Failed to join session. Please try again.')
      }
    }

    joinChannel()

    return () => {
      setIsJoined(false)
      localAudioTrack?.close()
      localVideoTrack?.close()
      screenTrack?.close()
      client.leave()
    }
  }, [credentials])

  // Toggle audio
  // setEnabled(true) = track active (unmuted), setEnabled(false) = track disabled (muted)
  const toggleAudio = async () => {
    if (localAudioTrack) {
      const newMuted = !isAudioMuted
      await localAudioTrack.setEnabled(!newMuted)
      setIsAudioMuted(newMuted)
    }
  }

  // Toggle video
  const toggleVideo = async () => {
    if (localVideoTrack) {
      const newMuted = !isVideoMuted
      await localVideoTrack.setEnabled(!newMuted)
      setIsVideoMuted(newMuted)
    }
  }

  // Start screen sharing
  const startScreenShare = async () => {
    try {
      const newScreenTrack = await AgoraRTC.createScreenVideoTrack({})

      if (localVideoTrack) {
        await client.unpublish([localVideoTrack])
        localVideoTrack.close()
      }

      // @ts-expect-error - Agora SDK types are narrower than the runtime shape
      await client.publish([newScreenTrack])
      // @ts-expect-error - newScreenTrack is the screen-only variant, not the full LocalVideoTrack
      setScreenTrack(newScreenTrack)
      setIsScreenSharing(true)
      toast.success('Screen sharing started')
    } catch (error) {
      console.error('Failed to start screen sharing:', error)
      toast.error('Failed to start screen sharing')
    }
  }

  // Stop screen sharing
  const stopScreenShare = async () => {
    try {
      if (screenTrack) {
        await client.unpublish([screenTrack])
        screenTrack.close()
        setScreenTrack(null)
      }

      const videoTrack = await AgoraRTC.createCameraVideoTrack()
      setLocalVideoTrack(videoTrack)

      if (localVideoRef.current) {
        videoTrack.play(localVideoRef.current)
      }

      await client.publish([videoTrack])
      setIsScreenSharing(false)
      toast.success('Screen sharing stopped')
    } catch (error) {
      console.error('Failed to stop screen sharing:', error)
      toast.error('Failed to stop screen sharing')
    }
  }

  // Leave webinar
  const handleLeave = async () => {
    try {
      localAudioTrack?.close()
      localVideoTrack?.close()
      screenTrack?.close()
      await client.leave()
      onLeave()
    } catch (error) {
      console.error('Failed to leave:', error)
      onLeave()
    }
  }

  // Waiting room UI
  if (inWaitingRoom) {
    return (
      <div className="fixed inset-0 bg-gray-900 z-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-white mx-auto mb-6"></div>
          <h2 className="text-white text-2xl font-semibold mb-2">Waiting Room</h2>
          <p className="text-gray-400">Waiting for the host to go live...</p>
          <button
            onClick={onLeave}
            className="mt-8 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition"
          >
            Leave Waiting Room
          </button>
        </div>
      </div>
    )
  }

  // Loading state while fetching credentials
  if (!credentials) {
    return (
      <div className="fixed inset-0 bg-gray-900 z-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-white mx-auto mb-6"></div>
          <h2 className="text-white text-2xl font-semibold mb-2">Connecting...</h2>
          <p className="text-gray-400">Setting up the webinar session</p>
        </div>
      </div>
    )
  }

  // Adaptive grid classes based on participant count (matching video call room)
  const getGridClasses = () => {
    const count = displayParticipants.length
    if (count <= 1) return 'grid-cols-1'
    if (count === 2) return 'grid-cols-1 md:grid-cols-2'
    if (count <= 4) return 'grid-cols-2 grid-rows-2'
    return 'grid-cols-2 md:grid-cols-3'
  }

  return (
    <div className="fixed inset-0 bg-gray-900 z-50 flex flex-col">
      {/* Top Bar */}
      <div className="bg-gray-800/90 backdrop-blur-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-white font-medium text-sm">{isHost ? 'LIVE' : 'WATCHING'}</span>
          </div>
          <span className="text-gray-400 text-xs hidden sm:inline">
            {displayParticipants.length} participant{displayParticipants.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleParticipants}
            className={`p-2 rounded-lg text-white transition cursor-pointer ${
              showParticipants ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <UsersIcon size={20} />
          </button>
          <button
            onClick={toggleChat}
            className={`relative p-2 rounded-lg text-white transition cursor-pointer ${
              showChat ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <ChatCircleIcon size={20} />
            {unreadCount > 0 && !showChat && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center text-white font-medium">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Video Area */}
        <div className="flex-1 flex items-stretch p-2 md:p-4 relative overflow-hidden">
          <div className={`grid ${getGridClasses()} gap-2 md:gap-3 w-full h-full`}>
            {displayParticipants.map((participant) => {
              const isSelf = participant.userId === userId
              const remoteUser = remoteUsers.find(
                (u) => String(u.uid) === participant.userId,
              )
              const hasVideo = isSelf ? !isVideoMuted : !!remoteUser?.videoTrack

              return (
                <div
                  key={participant.userId}
                  className="relative bg-gray-800 rounded-xl overflow-hidden"
                >
                  {/* Self local video */}
                  {isSelf && (
                    <div
                      ref={localVideoRef}
                      className={`w-full h-full ${isVideoMuted ? 'hidden' : ''}`}
                      style={{ minHeight: 0 }}
                    ></div>
                  )}

                  {/* Remote user video */}
                  {!isSelf && remoteUser?.videoTrack && (
                    <div
                      ref={(ref) => {
                        if (ref && remoteUser.videoTrack) {
                          remoteUser.videoTrack.play(ref)
                        }
                      }}
                      className="w-full h-full"
                      style={{ minHeight: 0 }}
                    ></div>
                  )}

                  {/* Avatar placeholder when no video */}
                  {!hasVideo && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-700">
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-gray-600 flex items-center justify-center">
                          <span className="text-3xl md:text-4xl text-white font-semibold">
                            {participant.userName.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="text-gray-400 text-sm">
                          {isSelf ? 'You' : participant.userName}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Raised hand indicator */}
                  {participant.handRaised && (
                    <div className="absolute top-3 right-3 animate-bounce">
                      <div className="bg-yellow-500 p-1.5 rounded-full">
                        <HandPalmIcon size={20} weight="fill" className="text-white" />
                      </div>
                    </div>
                  )}

                  {/* Name badge with audio level */}
                  <div className="absolute bottom-3 left-3">
                    <div className="bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-lg text-white text-sm font-medium flex items-center gap-2">
                      <AudioLevelIndicator
                        level={isSelf ? localAudioLevel : (remoteAudioLevels[participant.userId] ?? 0)}
                        isMuted={mutedUserIds.has(participant.userId)}
                      />
                      {participant.userName}
                      {isSelf ? ' (You)' : ''}
                      {participant.isHost && !isSelf ? ' (Host)' : ''}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* No Participants Overlay */}
          {!isHost && remoteUsers.length === 0 && displayParticipants.length <= 1 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="bg-black/40 backdrop-blur-sm px-6 py-4 rounded-xl text-center">
                <p className="text-white text-lg font-medium">
                  Waiting for host to start...
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Participants Panel */}
        {showParticipants && (
          <WebinarParticipantsPanel
            participants={displayParticipants}
            currentUserId={userId}
            isHost={isHost}
            mutedUserIds={mutedUserIds}
            localAudioLevel={localAudioLevel}
            remoteAudioLevels={remoteAudioLevels}
            onKickUser={rtm.kickUser}
            onMuteAll={async () => {
              await rtm.muteAllAudience()
              toast.success('All audience members have been muted')
            }}
            onDismissHand={rtm.dismissHand}
            onClose={() => setShowParticipants(false)}
          />
        )}

        {/* Chat Panel */}
        {showChat && (
          <WebinarChatPanel
            chatMessages={rtm.chatMessages}
            onSendMessage={rtm.sendChatMessage}
            currentUserId={userId}
            onClose={() => setShowChat(false)}
          />
        )}
      </div>

      {/* Controls Bar (Bottom) */}
      <div className="bg-gray-800 p-4 flex items-center justify-center gap-4">
        {/* Audio Toggle */}
        <button
          onClick={toggleAudio}
          className={`p-4 rounded-full transition cursor-pointer ${
            isAudioMuted ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-700 hover:bg-gray-600'
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
            isVideoMuted ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          {isVideoMuted ? (
            <VideoCameraSlashIcon size={24} className="text-white" />
          ) : (
            <VideoCameraIcon size={24} className="text-white" />
          )}
        </button>

        {/* Host-only: Screen Share */}
        {isHost && (
          <button
            onClick={isScreenSharing ? stopScreenShare : startScreenShare}
            className={`p-4 rounded-full transition cursor-pointer ${
              isScreenSharing ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <MonitorIcon size={24} className="text-white" />
          </button>
        )}

        {/* Audience-only: Raise Hand */}
        {!isHost && (
          <button
            onClick={rtm.myHandRaised ? rtm.lowerHand : rtm.raiseHand}
            className={`p-4 rounded-full transition cursor-pointer ${
              rtm.myHandRaised
                ? 'bg-yellow-500 hover:bg-yellow-600'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title={rtm.myHandRaised ? 'Lower Hand' : 'Raise Hand'}
          >
            <HandPalmIcon
              size={24}
              weight={rtm.myHandRaised ? 'fill' : 'regular'}
              className={rtm.myHandRaised ? 'text-black' : 'text-white'}
            />
          </button>
        )}

        {/* Leave */}
        <button
          onClick={handleLeave}
          className="p-4 bg-red-600 hover:bg-red-700 rounded-full transition ml-4 cursor-pointer"
        >
          <PhoneDisconnectIcon size={24} className="text-white" />
        </button>
      </div>
    </div>
  )
}

export default AgoraWebinarRoom
