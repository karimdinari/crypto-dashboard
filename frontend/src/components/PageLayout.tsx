import type { ReactNode } from 'react'

/** Consistent horizontal rhythm and max width for secondary pages. */
export function PageLayout({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div
      className={`mx-auto w-full max-w-6xl px-3 py-5 md:px-5 md:py-7 ${className}`}
    >
      {children}
    </div>
  )
}
