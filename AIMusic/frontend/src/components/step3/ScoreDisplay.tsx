import { useEffect, useRef } from 'react'
import abcjs from 'abcjs'

interface ScoreDisplayProps {
  abcNotation: string
}

export default function ScoreDisplay({ abcNotation }: ScoreDisplayProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current || !abcNotation.trim()) return

    containerRef.current.innerHTML = ''

    try {
      abcjs.renderAbc(containerRef.current, abcNotation, {
        responsive: 'resize',
        staffwidth: 680,
        paddingtop: 10,
        paddingbottom: 10,
        paddingright: 20,
        paddingleft: 20,
      })
    } catch {
      containerRef.current.innerHTML = '<p class="text-vermilion-light text-sm">曲谱渲染失败，请检查ABC记谱法格式</p>'
    }
  }, [abcNotation])

  if (!abcNotation.trim()) {
    return (
      <div className="bg-ink-light border border-gold/20 rounded-xl p-6 text-center">
        <p className="text-rice-dark text-sm">尚未生成曲谱</p>
      </div>
    )
  }

  return (
    <div className="bg-rice/5 border border-gold/20 rounded-xl p-4 overflow-auto">
      <div ref={containerRef} className="min-h-[120px]" />
    </div>
  )
}
