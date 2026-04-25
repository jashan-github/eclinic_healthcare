import type { FC } from 'react'
import WebinarTabs from './webinar-tabs'
// import { LiveWebinarContent } from './live-webinar-content'
import { UpcomingWebinarContent } from './upcoming-webinar'
import { PastWebinarContent } from './past-webinar'

const WebinarContent: FC = () => {
    return (
        <div className="bg-white rounded-lg shadow-[6px_7px_20px_0px_#0000001A] pb-6">
            <div className="mx-auto px-6 py-6">
                {/* <div className="bg-gray-100 p-4 rounded-md">
                    <div className="mx-auto p-2">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="flex items-center gap-2 text-[#B91C1C] font-poppins font-medium">
                                    <span className="font-poppins font-medium text-[20px] leading-6 tracking-[-0.6px] w-2 h-2 bg-[#EF4444] rounded-full"></span>
                                    Live Webinar
                                </span>
                            </div>
                        </div>
                    </div>
                    <LiveWebinarContent />
                </div> */}
            </div>

            <div className='px-6'>
                <WebinarTabs
                tabs={[
                    {
                        label: 'Upcoming',
                        value: 'upcoming',
                        content: (
                            <UpcomingWebinarContent />
                        ),
                    },
                    {
                        label: 'Past Webinar',
                        value: 'past',
                        content: (
                            <PastWebinarContent />
                        ),
                    },
                ]}
            />
            </div>
        </div>
    )
}

export default WebinarContent
