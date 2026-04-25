// // src/features/socket/use-all-chat-channels.ts

// import { useEffect, useState, useRef } from 'react';
// import echo from './pusher';

// interface IncomingMessage {
//   chatId: string;
//   message: any;
//   received_at: string;
// }

// /**
//  * Hook to subscribe to multiple chat channels at once
//  * Subscribes when user lands on messages page, not on individual chat click
//  */
// export const useAllChatChannels = (
//   chatIds: string[],
//   onMessageReceived?: (data: IncomingMessage) => void
// ) => {
//   const [connectedChannels, setConnectedChannels] = useState<Set<string>>(new Set());
//   const [connectionErrors, setConnectionErrors] = useState<Map<string, string>>(new Map());

//   // Store callback in ref to avoid re-subscriptions
//   const onMessageReceivedRef = useRef(onMessageReceived);

//   // Track currently subscribed channel IDs
//   const subscribedChannelsRef = useRef<Set<string>>(new Set());

//   // Track bound handlers for cleanup
//   const handlersRef = useRef<Map<string, {
//     onSuccess: () => void;
//     onError: (e: any) => void;
//     onMessage: (d: any) => void;
//   }>>(new Map());

//   // Store chatIds in ref for comparison
//   const chatIdsRef = useRef<string[]>([]);

//   // Update callback ref when it changes
//   useEffect(() => {
//     onMessageReceivedRef.current = onMessageReceived;
//   }, [onMessageReceived]);

//   // Main subscription effect
//   useEffect(() => {
//     const pusher = echo.connector.pusher;

//     // Check what changed
//     const currentIds = new Set(chatIds);
//     const previousIds = new Set(chatIdsRef.current);

//     // Find new channels to subscribe
//     const toSubscribe = chatIds.filter(id => !previousIds.has(id));
//     // Find channels to unsubscribe (removed from list)
//     const toUnsubscribe = chatIdsRef.current.filter(id => !currentIds.has(id));

//     // Update ref
//     chatIdsRef.current = [...chatIds];

//     // Skip if nothing changed
//     if (toSubscribe.length === 0 && toUnsubscribe.length === 0) {
//       console.log('📡 No channel changes detected');
//       return;
//     }

//     // Reconnect if needed
//     const connectionState = pusher.connection.state;
//     if (connectionState === 'disconnected' || connectionState === 'failed') {
//       pusher.connect();
//     }

//     // Unsubscribe from removed channels
//     toUnsubscribe.forEach(chatId => {
//       const channelName = `chat.${chatId}`;
//       console.log(`🔌 Unsubscribing from removed channel: ${channelName}`);

//       try {
//         const channel = pusher.channel(channelName);
//         const handlers = handlersRef.current.get(chatId);

//         if (channel && handlers) {
//           channel.unbind('pusher:subscription_succeeded', handlers.onSuccess);
//           channel.unbind('pusher:subscription_error', handlers.onError);
//           channel.unbind('.message.sent', handlers.onMessage);
//           channel.unbind('message.sent', handlers.onMessage);
//           channel.unbind('MessageSent', handlers.onMessage);
//           channel.unbind('message', handlers.onMessage);
//         }

//         pusher.unsubscribe(channelName);
//         subscribedChannelsRef.current.delete(chatId);
//         handlersRef.current.delete(chatId);

//         setConnectedChannels(prev => {
//           const next = new Set(prev);
//           next.delete(chatId);
//           return next;
//         });
//       } catch (error) {
//         console.error(`Error unsubscribing from ${channelName}:`, error);
//       }
//     });

//     // Subscribe to new channels
//     toSubscribe.forEach(chatId => {
//       // Skip if already subscribed
//       if (subscribedChannelsRef.current.has(chatId)) {
//         console.log(`📡 Already subscribed to chat.${chatId}`);
//         return;
//       }

//       const channelName = `chat.${chatId}`;
//       console.log(`📡 Subscribing to new channel: ${channelName}`);

//       let channel = pusher.channel(channelName);

//       if (!channel) {
//         channel = pusher.subscribe(channelName);
//       } else if (channel.subscribed) {
//         console.log(`📡 Channel already active: ${channelName}`);
//         subscribedChannelsRef.current.add(chatId);
//         setConnectedChannels(prev => new Set([...prev, chatId]));
//         return;
//       }

//       // Create handlers
//       const onSuccess = () => {
//         console.log(`✅ Subscribed to channel: ${channelName}`);
//         setConnectedChannels(prev => new Set([...prev, chatId]));
//         setConnectionErrors(prev => {
//           const next = new Map(prev);
//           next.delete(chatId);
//           return next;
//         });
//       };

//       const onError = (error: any) => {
//         console.error(`❌ Subscription error for ${channelName}:`, error);
//         subscribedChannelsRef.current.delete(chatId);
//         setConnectionErrors(prev => {
//           const next = new Map(prev);
//           next.set(chatId, error?.message || 'Subscription failed');
//           return next;
//         });
//       };

//       const onMessage = (data: any) => {
//         console.log(`📨 Message received on ${channelName}:`, data);
//         onMessageReceivedRef.current?.({
//           chatId,
//           message: data,
//           received_at: new Date().toISOString(),
//         });
//       };

//       // Store handlers for later cleanup
//       handlersRef.current.set(chatId, { onSuccess, onError, onMessage });

//       // Bind events
//       channel.bind('pusher:subscription_succeeded', onSuccess);
//       channel.bind('pusher:subscription_error', onError);
//       channel.bind('.message.sent', onMessage);
//       channel.bind('message.sent', onMessage);
//       channel.bind('MessageSent', onMessage);
//       channel.bind('message', onMessage);

//       subscribedChannelsRef.current.add(chatId);
//     });

//     // No cleanup in this effect - we want subscriptions to persist
//   }, [chatIds]);

//   // Cleanup on component unmount
//   useEffect(() => {
//     const cleanup = () => {
//       if (subscribedChannelsRef.current.size === 0) return;

//       console.log('🔌 Cleaning up all subscriptions');
//       const pusher = echo.connector.pusher;

//       subscribedChannelsRef.current.forEach(chatId => {
//         const channelName = `chat.${chatId}`;
//         try {
//           pusher.unsubscribe(channelName);
//           console.log(`✅ Unsubscribed from: ${channelName}`);
//         } catch (error) {
//           console.error(`Error unsubscribing from ${channelName}:`, error);
//         }
//       });

//       subscribedChannelsRef.current.clear();
//       handlersRef.current.clear();
//     };

//     // Listen for page unload/refresh
//     window.addEventListener('beforeunload', cleanup);

//     return () => {
//       window.removeEventListener('beforeunload', cleanup);
//       cleanup();
//     };
//   }, []);

//   return {
//     connectedChannels,
//     connectionErrors,
//     isFullyConnected: chatIds.length > 0 && connectedChannels.size === chatIds.length,
//     connectedCount: connectedChannels.size,
//     totalCount: chatIds.length,
//   };
// };
