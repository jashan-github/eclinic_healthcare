// store/viewStore.ts
import { create } from 'zustand';

type View = 'list' | 'calendar';

interface ViewStore {
  view: View;
  setView: (view: View) => void;
}

export const useViewStore = create<ViewStore>((set) => ({
  view: 'list',
  setView: (view) => set({ view }),
}));