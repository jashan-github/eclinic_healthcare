// Temporary type declarations for agora-rtc-sdk-ng
// Install the actual package with: npm install agora-rtc-sdk-ng

declare module 'agora-rtc-sdk-ng' {
  export interface IAgoraRTCClient {
    setClientRole(role: 'host' | 'audience'): Promise<void>
    join(appId: string, channel: string, token: string | null, uid: string | number): Promise<void>
    leave(): Promise<void>
    publish(tracks: any[]): Promise<void>
    unpublish(tracks: any[]): Promise<void>
    subscribe(user: any, mediaType: string): Promise<void>
    on(event: string, callback: (...args: any[]) => void): void
  }

  export interface IAgoraRTCRemoteUser {
    uid: string | number
    videoTrack?: {
      play(element: HTMLElement): void
    }
    audioTrack?: {
      play(): void
    }
  }

  export interface ICameraVideoTrack {
    play(element: HTMLElement): void
    stop(): void
    close(): void
    setEnabled(enabled: boolean): Promise<void>
  }

  export interface IMicrophoneAudioTrack {
    play(): void
    stop(): void
    close(): void
    setEnabled(enabled: boolean): Promise<void>
  }

  const AgoraRTC: {
    createClient(config: { mode: string; codec: string }): IAgoraRTCClient
    createMicrophoneAudioTrack(): Promise<IMicrophoneAudioTrack>
    createCameraVideoTrack(): Promise<ICameraVideoTrack>
    createScreenVideoTrack(config?: any): Promise<any>
  }

  export default AgoraRTC
}

