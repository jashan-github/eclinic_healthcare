import { XCircleIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

interface SingleImageProps {
  id: string
  image: string

  deleteImage: (id: string) => void
}

const SingleImage: FC<SingleImageProps> = ({
  id,
  image,
  deleteImage
}): ReactElement => {
  return (
    <div className="relative w-32 h-32">
      <XCircleIcon
        className="absolute right-0 top-0 text-gray-400 hover:text-gray-600 transition cursor-pointer"
        onClick={() => deleteImage(id)}
      />
      <img
        src={image}
        alt="Clinic Logo"
        className="w-32 h-32 object-cover"
      />
    </div>
  )
}

export default SingleImage
