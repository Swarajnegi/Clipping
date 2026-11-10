import type {ReferenceEdit} from './types';

export type PictureBox = {x: number; y: number; w: number; h: number; radius: number};

// Explicit on new project specs; older band layouts retain their dimensions.
export const SQUARE_PICTURE_FRAME = {x: 50, y: 470, width: 980, height: 980, radius: 48};

export const frameSourceWidth = (sourceWidth: number, sourceHeight: number,
  box: PictureBox, requested?: number): number => {
  const coverWidth = Math.min(1, (sourceHeight * box.w) / box.h / sourceWidth);
  return Math.min(requested ?? coverWidth, coverWidth);
};

export const referencePictureBox = (edit: ReferenceEdit): PictureBox => {
  if (edit.frame) return {x: edit.frame.x, y: edit.frame.y, w: edit.frame.width,
    h: edit.frame.height, radius: edit.frame.radius ?? 0};
  const h = edit.bandHeight ?? 608;
  return {x: 0, y: (1920 - h) / 2, w: 1080, h, radius: 0};
};
