import { cva } from 'class-variance-authority'

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-indigo-600 text-white hover:bg-indigo-700',
        secondary: 'border border-slate-300 bg-white text-slate-800 hover:bg-slate-50',
        danger: 'bg-red-600 text-white hover:bg-red-700',
        ghost: 'text-slate-700 hover:bg-slate-100',
      },
      size: {
        sm: 'h-8 px-3',
        md: 'h-10 px-4',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)
