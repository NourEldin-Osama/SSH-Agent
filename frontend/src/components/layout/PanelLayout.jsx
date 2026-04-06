import { useState } from 'react'

export function PanelLayout({ left, right }) {
  const [split, setSplit] = useState(40)
  const [dragging, setDragging] = useState(false)

  const handleMouseDown = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleMouseMove = (e) => {
    if (!dragging) return
    const container = e.currentTarget.parentElement
    if (!container) return
    const rect = container.getBoundingClientRect()
    const newSplit = ((e.clientX - rect.left) / rect.width) * 100
    setSplit(Math.min(Math.max(newSplit, 20), 80))
  }

  const handleMouseUp = () => setDragging(false)

  return (
    <div
      className="flex-1 flex overflow-hidden"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div style={{ width: `${split}%` }} className="overflow-hidden border-r border-gray-800">
        {left}
      </div>
      <div
        onMouseDown={handleMouseDown}
        className="w-1 bg-gray-800 hover:bg-blue-500 cursor-col-resize transition-colors flex-shrink-0"
      />
      <div style={{ width: `${100 - split}%` }} className="overflow-hidden">
        {right}
      </div>
    </div>
  )
}
