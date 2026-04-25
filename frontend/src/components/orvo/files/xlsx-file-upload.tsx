import { Button } from '@mantine/core'
import { DownloadIcon } from '@phosphor-icons/react'
import { useRef, type FC, type ReactElement } from 'react'

interface XlsxFileUploadProps {
  downloadSampleFile: () => void
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>
}

const XlsxFileUpload: FC<XlsxFileUploadProps> = ({
  downloadSampleFile,
  handleFileChange
}): ReactElement => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleButtonClick = () => {
    fileInputRef.current?.click() // Trigger the click event of the hidden file input
  }

  return (
    <>
      {/* Download Sample File Wrapper */}
      <div className="">
        <Button
          fullWidth
          variant={'transparent'}
          leftSection={<DownloadIcon size={16} />}
          onClick={downloadSampleFile}
        >
          Download Sample Excel
        </Button>
      </div>

      {/* Upload File Wrapper */}
      <div className="w-full">
        <input
          type="file"
          accept=".xls,.xlsx"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
        />
        <Button
          variant={'filled'}
          fullWidth
          className="cursor-pointer"
          onClick={handleButtonClick}
        >
          Upload
        </Button>
      </div>
    </>
  )
}

export default XlsxFileUpload
