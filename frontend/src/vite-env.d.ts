/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SECURE_LOCAL_STORAGE_HASH_KEY: string
  readonly VITE_SECURE_LOCAL_STORAGE_PREFIX: string
  // Add other environment variables here as needed
  [key: string]: string | boolean | undefined
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
