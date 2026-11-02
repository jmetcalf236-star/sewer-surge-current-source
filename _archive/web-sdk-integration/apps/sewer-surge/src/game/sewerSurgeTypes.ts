export type SewerPipeType = 'I' | 'L' | 'T' | 'X' | 'W' | 'S';
export type SewerScatterTier = 'none' | 'bonus' | 'deep-run';
export type SewerPipeCell = { t: SewerPipeType; r: 0 | 1 | 2 | 3; s: boolean };

export type BookEventSewerBoard = {
  index: number;
  type: 'sewerBoard';
  board: SewerPipeCell[][];
  inlet: number;
  scatterCount: number;
  scatterTier: SewerScatterTier;
  waterEntry: 'west';
  waterExit: 'east';
  routeAuthority: 'visual-only';
  schemaVersion: 1;
};

export type BookEventSewerFeature = {
  index: number;
  type: 'sewerFeature';
  feature: 'bonus' | 'deep-run';
  scatterCount: number;
  routeAuthority: 'visual-only';
};

export type BookEventSewerAward = {
  index: number;
  type: 'sewerAward';
  amount: number;
  payoutMultiplier: number;
  scatterTier: SewerScatterTier;
  maxWinCapped: boolean;
};

export type SewerSurgeRoundState = {
  board: SewerPipeCell[][];
  inlet: number;
  scatterCount: number;
  scatterTier: SewerScatterTier;
  payoutCents: number | null;
  maxWinCapped: boolean;
  bookId: string | number | null;
};
