// // src/hooks/use-chat-channel.ts

// import { useEffect, useState, useRef } from 'react';
// import echo from './pusher';

// /**
//  * React hook to listen to real-time messages in a chat
//  * @param chatId - The chat ID (string UUID)
//  * @param onMessageReceived - Callback jab message aaye
//  */

// export const useChatChannel = (
//   chatId: string | null,
//   onMessageReceived?: (message: any) => void
// ) => {
//   const [isConnected, setIsConnected] = useState(false);
//   const [lastReceivedMessage, setLastReceivedMessage] = useState<any>(null);
//   const [connectionError, setConnectionError] = useState<string | null>(null);

//   // Store callback in ref to avoid re-subscriptions when callback changes
//   const onMessageReceivedRef = useRef(onMessageReceived);

//   // Update ref when callback changes (without triggering effect)
//   useEffect(() => {
//     onMessageReceivedRef.current = onMessageReceived;
//   }, [onMessageReceived]);

//   useEffect(() => {
//     if (!chatId) {
//       console.log('⚠️ No chatId provided, skipping channel subscription');
//       setIsConnected(false);
//       setConnectionError(null);
//       return;
//     }

//     // Check WebSocket connection state
//     const pusher = echo.connector.pusher;
//     const connectionState = pusher.connection.state;
    
//     console.log(`🔄 Setting up channel subscription for chat.${chatId}, WebSocket state: ${connectionState}`);
    
//     if (connectionState !== 'connected' && connectionState !== 'connecting') {
//       console.warn('⚠️ WebSocket not connected. Current state:', connectionState);
//       // Attempt to connect if disconnected
//       if (connectionState === 'disconnected' || connectionState === 'failed') {
//         pusher.connect();
//       }
//     }

//     const channelName = `chat.${chatId}`;
    
//     // Check if channel already exists
//     let channel = pusher.channel(channelName);
    
//     if (!channel) {
//       console.log(`📡 Subscribing to channel: ${channelName}`);
//       channel = pusher.subscribe(channelName);
//     } else {
//       console.log(`📡 Channel already exists: ${channelName}, subscribed: ${channel.subscribed}`);
//       // If already subscribed, mark as connected
//       if (channel.subscribed) {
//         setIsConnected(true);
//       }
//     }
    
//     // Handler for subscription success
//     const onSubscriptionSucceeded = () => {
//       console.log(`✅ Successfully subscribed to channel: ${channelName}`);
//       setIsConnected(true);
//       setConnectionError(null);
//     };
    
//     // Handler for subscription errors
//     const onSubscriptionError = (error: any) => {
//       console.error(`❌ Channel Subscription Error for ${channelName}:`, error);
//       setIsConnected(false);
      
//       let errorMessage = 'Failed to connect to chat channel';
//       if (error?.status === 401 || error?.status === 403) {
//         errorMessage = 'Authentication failed. Please log in again.';
//       } else if (error?.message) {
//         errorMessage = error.message;
//       }
      
//       setConnectionError(errorMessage);
//     };

//     // Handler for incoming messages - try multiple event name formats
//     const onMessageReceivedHandler = (data: any) => {
//       console.log('✅ Message Received via WebSocket:', {
//         channel: channelName,
//         chat_id: chatId,
//         event_data: data,
//         received_at: new Date().toISOString(),
//       });

//       const enrichedMessage = {
//         ...data,
//         received_at: new Date().toISOString(),
//       };

//       setLastReceivedMessage(enrichedMessage);
//       onMessageReceivedRef.current?.(enrichedMessage);
//     };
    
//     // Override bind to log ALL events for debugging BEFORE binding
//     const originalBind = channel.bind.bind(channel);
//     (channel.bind as any) = function(this: any, eventName: string, callback: Function) {
//       if (!eventName.startsWith('pusher:')) {
//         console.log(`🔗 Binding to event: "${eventName}" on channel: ${channelName}`);
//       }
//       return originalBind.call(this, eventName, (...args: any[]) => {
//         // Log when events fire
//         if (!eventName.startsWith('pusher:')) {
//           console.log(`📨 [EVENT] "${eventName}" fired on ${channelName}:`, args[0]);
//         }
//         return callback(...args);
//       });
//     };
    
//     // Bind subscription events
//     console.log(`🔗 Setting up event listeners for channel: ${channelName}`);
//     channel.bind('pusher:subscription_succeeded', onSubscriptionSucceeded);
//     channel.bind('pusher:subscription_error', onSubscriptionError);
    
//     // Bind message events - try different event name formats that backend might use
//     // Laravel Echo typically uses events like ".message.sent" (with dot prefix)
//     console.log(`🔗 Binding to event formats: .message.sent, message.sent, MessageSent, message`);
//     channel.bind('.message.sent', onMessageReceivedHandler);
//     channel.bind('message.sent', onMessageReceivedHandler);
//     channel.bind('MessageSent', onMessageReceivedHandler);
//     channel.bind('message', onMessageReceivedHandler);
    
//     // For public channels, subscription might succeed immediately
//     // Check subscription status after a brief delay
//     setTimeout(() => {
//       if (channel.subscribed && !isConnected) {
//         console.log(`✅ Channel ${channelName} is already subscribed (checked after delay)`);
//         setIsConnected(true);
//       }
//     }, 500);

//     // Handle subscription timeout
//     const timeoutId = setTimeout(() => {
//       if (!isConnected) {
//         console.warn(`⚠️ Channel subscription timeout for: ${channelName}`);
//         setConnectionError('Connection timeout. Please try again.');
//       }
//     }, 10000); // 10 second timeout

//     // Cleanup
//     return () => {
//       clearTimeout(timeoutId);
//       console.log(`🔌 Cleaning up channel: ${channelName}`);
      
//       // Unbind all event listeners
//       channel.unbind('pusher:subscription_succeeded', onSubscriptionSucceeded);
//       channel.unbind('pusher:subscription_error', onSubscriptionError);
//       channel.unbind('.message.sent', onMessageReceivedHandler);
//       channel.unbind('message.sent', onMessageReceivedHandler);
//       channel.unbind('MessageSent', onMessageReceivedHandler);
//       channel.unbind('message', onMessageReceivedHandler);
      
//       try {
//         pusher.unsubscribe(channelName);
//         console.log(`✅ Unsubscribed from channel: ${channelName}`);
//       } catch (error) {
//         console.error('Error unsubscribing from channel:', error);
//       }
      
//       setIsConnected(false);
//       setConnectionError(null);
//     };
//   }, [chatId]); // Only re-subscribe when chatId changes

//   return {
//     isConnected,
//     lastMessage: lastReceivedMessage,
//     error: connectionError,
//   };
// };