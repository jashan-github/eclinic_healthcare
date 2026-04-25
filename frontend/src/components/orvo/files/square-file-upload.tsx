import { useClinicPhotos } from '@/features/app/my-profile/hooks/use-clinic-photos'
import type { ClinicPhotoRaw, ClinicPhotoType } from '@/types/clinic'
import { FileInput } from '@mantine/core'
import { FileArrowUpIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

type SquareFileUploadProps = {
  type: ClinicPhotoType
  maxFiles?: number
}

const SquareFileUpload: FC<SquareFileUploadProps> = ({
  type
}): ReactElement => {
  const { saveClinicPhoto, isSaving } = useClinicPhotos()
  const [value, setValue] = useState<File | null>(null)

  const handleUpload = (file: File | null) => {
    if (file) {
      const photoData: ClinicPhotoRaw = { image: file, type }
      saveClinicPhoto(photoData)
      setValue(null) // Reset input after upload
    }
  }

  return (
    <div className="relative w-40 h-40 flex items-center justify-center border-2 border-solid border-gray-200 rounded bg-[#F4F6F9] hover:bg-gray-200 transition-colors">
      <FileInput
        id="file-upload"
        className="absolute inset-0 opacity-0 cursor-pointer"
        accept="image/*"
        disabled={isSaving}
        value={value}
        onChange={handleUpload} // Consolidated
      />
      <FileArrowUpIcon className="w-12 h-12 text-gray-500" />
      <label
        htmlFor="file-upload"
        className="absolute inset-0 flex items-center justify-center cursor-pointer"
      >
        <span className="sr-only">Upload file</span>
      </label>
    </div>
  )
}

export default SquareFileUpload
