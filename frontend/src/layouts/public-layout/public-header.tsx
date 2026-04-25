// import { Button } from '@mantine/core'
import { Button } from '@mantine/core'
import { type FC, type ReactElement } from 'react'

const PublicHeader: FC = (): ReactElement => {
  const handleBack = () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = '/';
    }
  };
  
  return (
    <div className="w-full h-[60px] flex items-center justify-between border-b border-gray-200 shadow mx-auto sticky top-0 z-10 bg-white">
      <div className="container mx-auto flex items-center justify-between">
        <a href="/">
          <img
            className="h-10"
            src="/assets/icons/e-clinic-logo-full.svg"
            alt="Salutogena"
          />
        </a>

        <div className="flex justify-end gap-md">
          <Button
            variant="filled"
            onClick={handleBack}
            className="px-8 py-3 text-lg"
          >
            Back
          </Button>
        </div>
      </div>
    </div>
  )
}

export default PublicHeader
