import AppLayout from './components/layout/AppLayout'
import { useMusicStore } from './store/musicStore'
import PromptStep from './components/step1/PromptStep'
import LyricStep from './components/step2/LyricStep'
import ScoreStep from './components/step3/ScoreStep'
import MidiStep from './components/step4/MidiStep'

const stepComponents = [PromptStep, LyricStep, ScoreStep, MidiStep]

export default function App() {
  const { currentStep, loading, error } = useMusicStore()
  const StepComponent = stepComponents[currentStep] || PromptStep

  return (
    <AppLayout currentStep={currentStep}>
      {error && (
        <div className="mb-4 p-4 bg-vermilion/20 border border-vermilion/50 rounded-lg text-vermilion-light text-sm">
          {error}
        </div>
      )}
      {loading && (
        <div className="mb-4 p-4 bg-gold/10 border border-gold/30 rounded-lg text-gold text-sm text-center">
          正在处理中，请稍候...
        </div>
      )}
      <StepComponent />
    </AppLayout>
  )
}
