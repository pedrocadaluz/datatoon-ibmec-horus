import { useEffect, useState } from 'react'

export function useMobile() {
  const [mobile, setMobile] = useState(() => matchMedia('(max-width: 767px)').matches)
  useEffect(() => {
    const media = matchMedia('(max-width: 767px)')
    const change = () => setMobile(media.matches)
    media.addEventListener('change', change)
    return () => media.removeEventListener('change', change)
  }, [])
  return mobile
}
