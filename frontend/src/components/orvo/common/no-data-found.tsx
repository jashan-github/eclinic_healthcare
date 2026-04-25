import { type FC, type ReactElement } from 'react'

const NoDataFound: FC = (): ReactElement => {
  return (
    <div className="flex flex-col justify-center items-center w-full h-48">
      <img
        className="w-20"
        src="/assets/icons/no-data.svg"
        alt="No data found"
      />
      <div className="text-xl font-bold">No data found!!</div>
    </div>
  )
}

export default NoDataFound
