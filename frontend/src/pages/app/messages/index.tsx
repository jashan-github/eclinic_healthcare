import MessageContent from '@/features/app/messages/components/message-content'
import { type FC, type ReactElement } from 'react'

const MessagesPage: FC = (): ReactElement => {
  return (
    <div className="space-y-5 h-full w-full overflow-auto bg-[#F4F6F9] p-6">
      <div className="font-poppins font-medium text-lg leading-6 align-middle text-[#0F1011]">
        Communicate with your Patient
      </div>
      <MessageContent />
    </div>
  )
}

export default MessagesPage
