import { type FC, type ReactElement } from 'react'
import { useMyProfile } from '../../hooks/use-my-profile'
import { Card } from '@mantine/core'

const ClinicInformation: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()

  return (
    <Card className="orvo-base-card">
      <Card.Section>
        <div className="flex flex-col gap-4 justify-between">
          <div className="flex gap-2 justify-between">
            <div className="flex gap-2 items-center">
              <img
                className="w-20 h-auto"
                src="/assets/icons/profile_clinic.svg"
                alt={myProfile.active_clinic?.name}
              />
              <div className="">
                <div className="font-bold text-sm">
                  {myProfile.active_clinic?.name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {myProfile.active_clinic?.primary_address?.country}
                </div>
              </div>
            </div>

            {/* Clinic timings wrapper */}
            <div className=""></div>
          </div>
          {/* Clinic Amenities wrappers */}
          <div className="flex gap-4">
            <div className="flex flex-col gap-2 text-sm">
              <div className="font-bold">Payment Mode Accepted:</div>
              <ul className="list-inside font-light list-disc">
                <li>Cash</li>
                <li>Credit/Debit Cards</li>
                <li>UPI</li>
              </ul>
            </div>
            <div className="flex flex-col gap-2 text-sm">
              <div className="font-bold">Covid Protocols:</div>
              <ul className="list-inside font-light capitalize list-disc">
                <li>appointment required</li>
                <li>mask required</li>
                <li>staff get temperature check</li>
                <li>staff require to disinfect surfaces between visits</li>
                <li>staff wear mask</li>
                <li>temperature check required</li>
                <li>walk in</li>
              </ul>
            </div>
            <div className="flex flex-col gap-2 text-sm">
              <div className="font-bold">Clinic Amenities:</div>
              <ul className="list-inside font-light capitalize list-disc">
                <li>assistive hearing loop</li>
                <li>gender neutral restroom</li>
                <li>restroom</li>
                <li>wheelchair accessible elevator</li>
                <li>wheelchair accessible entrance</li>
                <li>wheelchair accessible restroom</li>
                <li>wheelchair accessible seating</li>
              </ul>
            </div>
          </div>
        </div>
      </Card.Section>
    </Card>
  )
}

export default ClinicInformation
