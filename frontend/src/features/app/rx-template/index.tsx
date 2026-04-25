import { type FC, type ReactElement } from 'react'
import RxTemplatePreview from './rx-template-preview'
import RxTemplateConfig from './rx-template-config'

const RxTemplateWrapper: FC = (): ReactElement => {
  return (
    <div className="flex h-full p-4">
      {/* Left Section */}
      <div className="w-1/3">
        <RxTemplateConfig />
      </div>

      <div className="w-2/3">
        {/* Right Section */}
        <RxTemplatePreview />
      </div>
    </div>
  )
}

export default RxTemplateWrapper
