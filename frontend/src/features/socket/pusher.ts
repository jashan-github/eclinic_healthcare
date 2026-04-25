// // src/lib/echo-instance.ts

// import Echo from "laravel-echo";
// import Pusher from "pusher-js";
// import { tokenCookies } from "@/utils/cookies";

// (window as any).Pusher = Pusher;

// // Function to get auth token dynamically
// const getAuthToken = (): string | null => {
//     if (typeof window === 'undefined') return null;
//     return tokenCookies.getAccessToken();
// };

// // Get initial token
// const initialToken = getAuthToken();

// const echo = new Echo({
//     broadcaster: "reverb",
//     Pusher,
//     key: (import.meta.env.VITE_WS_KEY as string),
//     wsHost: (import.meta.env.VITE_WS_HOST as string),
//     wsPort: import.meta.env.VITE_WS_PORT ? Number(import.meta.env.VITE_WS_PORT) : 8080,
//     forceTLS: false,
//     enabledTransports: ["ws"],
//     authEndpoint: (import.meta.env.VITE_WS_AUTH_ENDPOINT as string),
//     // Set up authorizer to read token dynamically on each subscription
//     // This will be called for private/presence channels, and can be extended for custom channels
//     authorizer: (channel: any, options: any) => {
//         return {
//             authorize: (socketId: string, callback: Function) => {
//                 // Read token fresh each time authorization is requested
//                 const token = getAuthToken();
                
//                 if (!token) {
//                     console.error("❌ Cannot authorize channel: No auth token found");
//                     callback(new Error("Authentication token not found"), null);
//                     return;
//                 }

//                 console.log(`🔐 Authorizing channel: ${channel.name} with socket_id: ${socketId}`);

//                 // Make authorization request to backend
//                 // The channel.name will be exactly as subscribed (e.g., "chat.123")
//                 // Backend should authorize this channel name format
//                 fetch(options.authEndpoint || `https://139.59.25.254/backend/api/broadcasting/auth`, {
//                     method: 'POST',
//                     headers: {
//                         'Content-Type': 'application/json',
//                         'Accept': 'application/json',
//                         'Authorization': `Bearer ${token}`,
//                     },
//                     body: JSON.stringify({
//                         socket_id: socketId,
//                         channel_name: channel.name, // This will be "chat.{chatId}" not "private-chat.{chatId}"
//                     }),
//                 })
//                 .then(response => {
//                     if (!response.ok) {
//                         return response.text().then(text => {
//                             throw new Error(`Authorization failed (${response.status}): ${text || response.statusText}`);
//                         });
//                     }
//                     return response.json();
//                 })
//                 .then(data => {
//                     console.log(`✅ Channel authorized successfully: ${channel.name}`);
//                     callback(null, data);
//                 })
//                 .catch(error => {
//                     console.error(`❌ Channel authorization error for ${channel.name}:`, error);
//                     callback(error, null);
//                 });
//             },
//         };
//     },
//     // Fallback auth headers (used if authorizer is not available)
//     auth: {
//         headers: initialToken ? {
//             Authorization: `Bearer ${initialToken}`,
//             Accept: 'application/json',
//         } : {
//             Accept: 'application/json',
//         },
//     },
// });

// // Connection event handlers
// echo.connector.pusher.connection.bind("connected", () => {
//     console.log("✅ WebSocket Connected Successfully!");
//     console.log("Connection State:", echo.connector.pusher.connection.state);
// });

// echo.connector.pusher.connection.bind("disconnected", () => {
//     console.warn("⚠️ WebSocket Disconnected");
// });

// echo.connector.pusher.connection.bind("error", (err: any) => {
//     console.error("❌ WebSocket Connection Error:", err);
//     console.error("Error Details:", {
//         type: err?.type,
//         error: err?.error,
//         message: err?.message,
//     });
// });

// // Handle subscription errors for private channels
// echo.connector.pusher.connection.bind("state_change", (states: any) => {
//     console.log("WebSocket State Change:", {
//         previous: states.previous,
//         current: states.current,
//     });
// });

// export default echo;