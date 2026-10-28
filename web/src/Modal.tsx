import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

/** Dialog nativo: foco contido, fundo inerte, Escape e retorno ao acionador. */
export function Modal({ open, onClose, title, className = '', children }: {
  open: boolean; onClose: () => void; title: string; className?: string; children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null)
  const trigger = useRef<HTMLElement | null>(null)
  useEffect(() => {
    const dialog = ref.current!
    if (!open) { if (dialog.open) dialog.close(); return }
    trigger.current = document.activeElement as HTMLElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialog.showModal()
    return () => {
      document.body.style.overflow = previousOverflow
      if (dialog.open) dialog.close()
      trigger.current?.focus({ preventScroll: true })
    }
  }, [open])
  return <dialog ref={ref} aria-label={title} className={`app-modal ${className}`} onCancel={onClose} onClick={e => { if (e.target === e.currentTarget) onClose() }}>
    <div className="modal-content">{children}</div>
  </dialog>
}
