import SquareFileUpload from '@/components/orvo/files/square-file-upload'
import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { Alert } from '@mantine/core'
import { InfoIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { useClinicPhotos } from '../../../hooks/use-clinic-photos'
import SingleImage from './single-image'

const Exterior: FC = (): ReactElement => {
  const { clinicPhotos, isLoading, error, deleteClinicPhoto } =
    useClinicPhotos()
  const interiorPhotos = clinicPhotos.filter(
    (photo) => photo.type.toLowerCase() === 'exterior'
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
        Post photos of the outside of your location so customers can find you
      </Alert>

      {/* Image Gallery */}
      <div className="flex gap-4 flex-wrap">
        {interiorPhotos.map((photo) => (
          <SingleImage
            deleteImage={(id) => deleteClinicPhoto(id)}
            {...photo}
          />
        ))}
        <SquareFileUpload type="exterior" />
      </div>
    </div>
  )
}

export default Exterior
