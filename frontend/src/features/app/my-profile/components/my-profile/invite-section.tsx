import {
  CopyIcon,
  LinkIcon,
  UserPlusIcon,
  type IconProps
} from '@phosphor-icons/react'
import {
  type FC,
  type ForwardRefExoticComponent,
  type ReactElement
} from 'react'
import { toast } from 'react-toastify'
import { useMyProfile } from '../../hooks/use-my-profile'

const InviteSection: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()

  return (
    <div className="bg-white rounded border-gray-300 border px-4 py-4 flex flex-col gap-2">
      <div className="">
        <div className="flex gap-5">
          {/* Invite Code Wrapper */}
          <div className="flex grow">
            <InviteCard
              icon={UserPlusIcon}
              label={'Invite Code'}
              title={myProfile?.invite_code || ''}
            />
          </div>

          {/* Invite Link Wrapper */}
          <div className="flex grow">
            <InviteCard
              icon={LinkIcon}
              label={'Invite Link'}
              title={myProfile?.invite_link || ''}
              isLink={true}
            />
          </div>
        </div>
      </div>
      <div className="bg-blue-100 text-sm font-thin rounded w-full p-4 flex gap-2 items-center">
        <LinkIcon className="text-primary" />
        Use the invite code to add Dr. {myProfile.name} to your list of healthcare providers
        on the EClinic App
      </div>
    </div>
  )
}

type InviteCardProps = {
  label: string
  icon: ForwardRefExoticComponent<IconProps>
  title: string
  isLink?: boolean
}

const InviteCard: FC<InviteCardProps> = ({
  label,
  icon,
  title,
  isLink = false
}): ReactElement => {
  const Icon = icon

  const copyToClipboard = (): void => {
    navigator.clipboard
      .writeText(title)
      .then(() => toast.success('Copied to clipboard'))
  }

  return (
    <div className="flex items-start gap-2">
      <div className="flex">
        <Icon />
      </div>
      <div className="flex flex-col gap-2 items-start">
        <div className="flex gap-4">
          <div className="text-lg">
            {isLink ? (
              <a
                className="underline hover:text-primary"
                href={title}
                target="_blank"
              >
                {title}
              </a>
            ) : (
              title
            )}
          </div>
          <div>
            <CopyIcon
              className="cursor-pointer"
              onClick={copyToClipboard}
            />
          </div>
        </div>
        <div className="text-xs">{label}</div>
      </div>
    </div>
  )
}

export default InviteSection
