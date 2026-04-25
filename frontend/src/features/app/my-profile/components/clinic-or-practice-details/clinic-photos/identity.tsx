import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import SquareFileUpload from '@/components/orvo/files/square-file-upload'
import { Alert } from '@mantine/core'
import { InfoIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { useClinicPhotos } from '../../../hooks/use-clinic-photos'
import SingleImage from './single-image'

// Only One Photo is allowed. A user can update the photo if needed.
const Identity: FC = (): ReactElement => {
  const { clinicPhotos, isLoading, error, deleteClinicPhoto } =
    useClinicPhotos()

  const identityPhoto = clinicPhotos.find(
    (photo) => photo.type.toLowerCase() === 'identity'
  )

  if (isLoading) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4 flex-col flex gap-4">
      {/* Alert Banner */}
      <Alert
        variant="light"
        color="blue"
        title=""
        icon={<InfoIcon />}
      >
        Add a photo of your clinic logo to help patients recognize
      </Alert>

      {/* Image Gallery */}
      <div className="flex gap-4 flex-wrap">
        {identityPhoto ? (
          <SingleImage
            deleteImage={(id) => deleteClinicPhoto(id)}
            {...identityPhoto}
          />
        ) : (
          <SquareFileUpload
            maxFiles={1}
            type="identity"
          />
        )}
      </div>
    </div>
  )
}

export default Identity
