import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import SquareFileUpload from '@/components/orvo/files/square-file-upload'
import { type FC, type ReactElement } from 'react'
import { useClinicPhotos } from '../../../hooks/use-clinic-photos'
import SingleImage from './single-image'
import { InfoIcon } from '@phosphor-icons/react'
import { Alert } from '@mantine/core'

const WithPatients: FC = (): ReactElement => {
  const { clinicPhotos, isLoading, error, deleteClinicPhoto } =
    useClinicPhotos()
  const interiorPhotos = clinicPhotos.filter(
    (photo) => photo.type.toLowerCase() === 'patients'
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
        Add a few photos of you sitting with your patients or treating them to
        build trust
      </Alert>

      {/* Image Gallery */}
      <div className="flex gap-4 flex-wrap">
        {interiorPhotos.map((photo) => (
          <SingleImage
            deleteImage={(id) => deleteClinicPhoto(id)}
            {...photo}
          />
        ))}
        <SquareFileUpload type="with-patient" />
      </div>
    </div>
  )
}

export default WithPatients
