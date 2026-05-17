interface StepIndicatorProps {
  currentStep: number
}

const steps = [
  { label: '提示词', num: '①' },
  { label: '歌词', num: '②' },
  { label: '曲谱', num: '③' },
  { label: 'MIDI', num: '④' },
]

export default function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-2">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center">
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 ${
              index === currentStep
                ? 'bg-gold text-ink shadow-lg shadow-gold/30'
                : index < currentStep
                  ? 'bg-green-600/20 text-green-400'
                  : 'bg-ink-light text-rice-dark'
            }`}
          >
            {index < currentStep ? (
              <span className="text-sm">✓</span>
            ) : (
              <span className="text-sm font-medium">{step.num}</span>
            )}
            <span className="text-sm font-medium">{step.label}</span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={`w-8 h-0.5 mx-1 transition-colors duration-300 ${
                index < currentStep ? 'bg-green-500' : 'bg-ink-light'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  )
}
