import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge condicional de classes Tailwind (padrão shadcn/ui). */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
