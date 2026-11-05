import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-blue-50 text-blue-700',
        secondary: 'border-transparent bg-slate-100 text-slate-600',
        success: 'border-transparent bg-emerald-50 text-emerald-700',
        warning: 'border-transparent bg-amber-50 text-amber-700',
        outline: 'border-slate-200 text-slate-600',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export function Badge({ className, variant, ...props }:
  React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
