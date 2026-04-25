import { useEffect, useRef, useState, useCallback } from 'react'
import type { IAgoraRTCClient } from 'agora-rtc-sdk-ng'

export interface ChatMessage {
  id: string
  senderId: string
  senderName: string
  text: string
  timestamp: number
}

export interface Participant {
  userId: string
  userName: string
  isHost: boolean
  handRaised: boolean
}

interface RtmMessage {
  type:
    | 'CHAT'
    | 'USER_JOINED'
    | 'USER_LEFT'
    | 'MUTE_ALL'
    | 'KICK_USER'
    | 'RAISE_HAND'
    | 'LOWER_HAND'
    | 'DISMISS_HAND'
  text?: string
  id?: string
  userName?: string
  isHost?: boolean
  isReply?: boolean
  targetUserId?: string
  senderId?: string
}

interface UseWebinarRtmParams {
  rtcClient: IAgoraRTCClient | null
  userId: string
  userName: string
  isHost: boolean
  enabled: boolean
}

export function useWebinarRtm({
  rtcClient,
  userId,
  userName,
  isHost,
  enabled,
}: UseWebinarRtmParams) {
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [participants, setParticipants] = useState<Participant[]>([])
  const [myHandRaised, setMyHandRaised] = useState(false)
  const [isKicked, setIsKicked] = useState(false)
  const [forceMuteCount, setForceMuteCount] = useState(0)
  const [isConnected, setIsConnected] = useState(false)

  const userIdRef = useRef(userId)
  userIdRef.current = userId

  const userNameRef = useRef(userName)
  userNameRef.current = userName

  const isHostRef = useRef(isHost)
  isHostRef.current = isHost

  // Send a message via RTC data stream
  const publishMessage = useCallback(
    async (msg: RtmMessage) => {
      if (!rtcClient) return
      try {
        const payload = JSON.stringify({ ...msg, senderId: userIdRef.current })
        await (rtcClient as any).sendStreamMessage(new TextEncoder().encode(payload))
      } catch (err) {
        console.error('[DataStream] Send error:', err)
      }
    },
    [rtcClient],
  )

  // Always add self to participants when enabled
  useEffect(() => {
    if (!enabled || !userId) return
    setParticipants((prev) => {
      if (prev.find((p) => p.userId === userId)) return prev
      return [...prev, { userId, userName, isHost, handRaised: false }]
    })
  }, [enabled, userId, userName, isHost])

  // RTC Data Stream setup
  useEffect(() => {
    if (!enabled || !rtcClient) return

    let isCancelled = false

    const handleStreamMessage = (_uid: number | string, data: Uint8Array) => {
      if (isCancelled) return
      let msg: RtmMessage
      try {
        msg = JSON.parse(new TextDecoder().decode(data))
      } catch {
        return
      }

      const senderId = msg.senderId || String(_uid)

      switch (msg.type) {
        case 'CHAT':
          setChatMessages((prev) => [
            ...prev,
            {
              id: msg.id || `${senderId}-${Date.now()}`,
              senderId,
              senderName: msg.userName || senderId,
              text: msg.text || '',
              timestamp: Date.now(),
            },
          ])
          break

        case 'USER_JOINED':
          setParticipants((prev) => {
            if (prev.find((p) => p.userId === senderId)) return prev
            return [
              ...prev,
              {
                userId: senderId,
                userName: msg.userName || senderId,
                isHost: msg.isHost || false,
                handRaised: false,
              },
            ]
          })
          // Reply so late joiners discover us
          if (!msg.isReply) {
            publishMessage({
              type: 'USER_JOINED',
              userName: userNameRef.current,
              isHost: isHostRef.current,
              isReply: true,
            })
          }
          break

        case 'USER_LEFT':
          setParticipants((prev) => prev.filter((p) => p.userId !== senderId))
          break

        case 'MUTE_ALL':
          if (!isHostRef.current) {
            setForceMuteCount((prev) => prev + 1)
          }
          break

        case 'KICK_USER':
          if (msg.targetUserId === userIdRef.current) {
            setIsKicked(true)
          }
          if (msg.targetUserId) {
            setParticipants((prev) =>
              prev.filter((p) => p.userId !== msg.targetUserId),
            )
          }
          break

        case 'RAISE_HAND':
          setParticipants((prev) => {
            const exists = prev.some((p) => p.userId === senderId)
            if (exists) {
              return prev.map((p) =>
                p.userId === senderId ? { ...p, handRaised: true } : p,
              )
            }
            // Participant not yet in list — add them
            return [
              ...prev,
              {
                userId: senderId,
                userName: msg.userName || senderId,
                isHost: false,
                handRaised: true,
              },
            ]
          })
          break

        case 'LOWER_HAND':
          setParticipants((prev) => {
            const exists = prev.some((p) => p.userId === senderId)
            if (exists) {
              return prev.map((p) =>
                p.userId === senderId ? { ...p, handRaised: false } : p,
              )
            }
            return [
              ...prev,
              {
                userId: senderId,
                userName: msg.userName || senderId,
                isHost: false,
                handRaised: false,
              },
            ]
          })
          break

        case 'DISMISS_HAND':
          if (msg.targetUserId) {
            setParticipants((prev) =>
              prev.map((p) =>
                p.userId === msg.targetUserId
                  ? { ...p, handRaised: false }
                  : p,
              ),
            )
            if (msg.targetUserId === userIdRef.current) {
              setMyHandRaised(false)
            }
          }
          break
      }
    }

    const setup = async () => {
      try {
        setIsConnected(true)
        console.log('[DataStream] Ready')

        // Broadcast join
        const payload = JSON.stringify({
          type: 'USER_JOINED',
          userName,
          isHost,
          isReply: false,
          senderId: userId,
        } satisfies RtmMessage)
        await (rtcClient as any).sendStreamMessage(new TextEncoder().encode(payload))
      } catch (err) {
        console.error('[DataStream] Setup error:', err)
      }
    }

    rtcClient.on('stream-message', handleStreamMessage)
    setup()

    return () => {
      isCancelled = true
      ;(rtcClient as any).off('stream-message', handleStreamMessage)
      setIsConnected(false)
      setChatMessages([])
      setMyHandRaised(false)
      setForceMuteCount(0)
      setParticipants((prev) => prev.filter((p) => p.userId === userId))
    }
  }, [enabled, rtcClient, userId, userName, isHost, publishMessage])

  // --- Actions ---

  const sendChatMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return
      const msgId = `${userId}-${Date.now()}`
      // Add locally immediately
      setChatMessages((prev) => [
        ...prev,
        {
          id: msgId,
          senderId: userId,
          senderName: userName,
          text: trimmed,
          timestamp: Date.now(),
        },
      ])
      await publishMessage({
        type: 'CHAT',
        text: trimmed,
        id: msgId,
        userName,
      })
    },
    [userId, userName, publishMessage],
  )

  const muteAllAudience = useCallback(async () => {
    await publishMessage({ type: 'MUTE_ALL' })
  }, [publishMessage])

  const kickUser = useCallback(
    async (targetUserId: string) => {
      await publishMessage({ type: 'KICK_USER', targetUserId })
      setParticipants((prev) =>
        prev.filter((p) => p.userId !== targetUserId),
      )
    },
    [publishMessage],
  )

  const dismissHand = useCallback(
    async (targetUserId: string) => {
      await publishMessage({ type: 'DISMISS_HAND', targetUserId })
      setParticipants((prev) =>
        prev.map((p) =>
          p.userId === targetUserId ? { ...p, handRaised: false } : p,
        ),
      )
    },
    [publishMessage],
  )

  const raiseHand = useCallback(async () => {
    setMyHandRaised(true)
    setParticipants((prev) =>
      prev.map((p) =>
        p.userId === userIdRef.current ? { ...p, handRaised: true } : p,
      ),
    )
    await publishMessage({ type: 'RAISE_HAND', userName: userNameRef.current })
  }, [publishMessage])

  const lowerHand = useCallback(async () => {
    setMyHandRaised(false)
    setParticipants((prev) =>
      prev.map((p) =>
        p.userId === userIdRef.current ? { ...p, handRaised: false } : p,
      ),
    )
    await publishMessage({ type: 'LOWER_HAND', userName: userNameRef.current })
  }, [publishMessage])

  return {
    isConnected,
    chatMessages,
    sendChatMessage,
    participants,
    muteAllAudience,
    kickUser,
    dismissHand,
    raiseHand,
    lowerHand,
    myHandRaised,
    isKicked,
    forceMuteCount,
  }
}
