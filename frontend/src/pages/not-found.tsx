import { Button } from '@mantine/core'
import { Link } from '@tanstack/react-router'
import type { FC, ReactElement } from 'react'

const NotFound: FC = (): ReactElement => {
  return (
    <div className="h-screen min-h-screen flex justify-center items-center bg-[#F4F6F9]">
      <div className="bg-white shadow rounded-3xl min-h-[400px] min-w-2xl p-6 flex justify-center items-center gap-5 flex-col">
        <img
          className="w-[100px]"
          src="/assets/icons/error-page-not-found.svg"
          alt=""
        />
        <div className="text-xl font-bold">Page Not Found</div>
        <div className="flex justify-center gap-2">
          <Button variant={'link'}>
            <Link to={'/'}>Go to Home</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

export default NotFound
