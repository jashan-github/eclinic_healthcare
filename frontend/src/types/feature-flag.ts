export type FeatureFlagsType = Record<
  string,
  { enabled: boolean; dev: boolean; staging: boolean; production: boolean }
>
