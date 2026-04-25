// src/hooks/use-chat-encryption.ts

import { isEncryptionSupported } from '@/utils/helper';
import { useState, useEffect } from 'react';

const deriveEncryptionKey = async (sharedSecret: string): Promise<CryptoKey> => {
  const encoder = new TextEncoder();
  const salt = encoder.encode('chat-salt');
  const baseKey = await crypto.subtle.importKey(
    'raw',
    encoder.encode(sharedSecret),
    'PBKDF2',
    false,
    ['deriveBits', 'deriveKey']
  );

  return await crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
};

export const useChatEncryption = (roomId: string | null, sharedSecret: string) => {
  const [encryptionKey, setEncryptionKey] = useState<CryptoKey | null>(null);
  const [isEncryptionReady, setIsEncryptionReady] = useState(false);

  useEffect(() => {
    if (!roomId || !sharedSecret) return;

    if (!isEncryptionSupported) {
      setIsEncryptionReady(false);
      return;
    }

    const initEncryption = async () => {
      try {
        const key = await deriveEncryptionKey(sharedSecret);
        setEncryptionKey(key);
        setIsEncryptionReady(true);
      } catch (err) {
        console.error('Encryption init error:', err);
      }
    };

    initEncryption();
  }, [roomId, sharedSecret]);


  const encryptMessage = async (plainText: string): Promise<string> => {
    if (!isEncryptionSupported) {
      return plainText;
    }

    if (!encryptionKey) throw new Error('Encryption key not ready');

    const encoder = new TextEncoder();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      encryptionKey,
      encoder.encode(plainText)
    );

    // Combine IV + encrypted into base64
    const combined = new Uint8Array(iv.byteLength + encrypted.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(encrypted), iv.byteLength);
    return btoa(String.fromCharCode(...combined));
  };

  const decryptMessage = async (encryptedBase64: string): Promise<string> => {
    if (!isEncryptionSupported) return encryptedBase64;
    if (!encryptionKey) return encryptedBase64;
    if (!encryptedBase64 || typeof encryptedBase64 !== 'string') return encryptedBase64;

    let combined: Uint8Array;

    try {
      combined = Uint8Array.from(atob(encryptedBase64), c => c.charCodeAt(0));
    } catch {
      // not valid base64 → plain text
      return encryptedBase64;
    }

    if (combined.length <= 12) return encryptedBase64;

    try {
      const iv = combined.slice(0, 12);
      const encrypted = combined.slice(12);

      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        encryptionKey,
        encrypted
      );

      return new TextDecoder().decode(decrypted);
    } catch {
      // decrypt failed → fallback
      return encryptedBase64;
    }
  };

  return { isEncryptionReady, encryptMessage, decryptMessage };
};