import HeadSubhead from '@/components/ui/head-subhead'
import { useState, type FC, type ReactElement } from 'react'
import { CurrencyDollarIcon, UsersIcon, CameraIcon, PlusIcon } from '@phosphor-icons/react'
import { SingleCard } from '@/components/e-clinic/admin/dashboard/single-card'
import WebinarsCard from '@/components/e-clinic/admin/webinars/webinars-card'
import WebinarDialog from '@/components/e-clinic/admin/webinars/webinar-dialog'

const cards = [
    { id: 1, title: 'Total Webinars', value: 60, Icon: CameraIcon },
    { id: 2, title: 'Total Participants', value: 1500, Icon: UsersIcon },
    { id: 3, title: 'Revenue', value: 15346, Icon: CurrencyDollarIcon },
]

const AdminWebinar: FC = (): ReactElement => {
    const [isDialogOpen, setIsDialogOpen] = useState(false)

    return (
        <>
            <div className="h-screen overflow-auto bg-[#F4F6F9]">
                <div className="p-4 h-full">
                    <div className="flex justify-between items-center p-6">
                        <HeadSubhead
                            head={'Webinar Management'}
                            subhead={'Create and manage educational webinars'}
                        />
                        <button
                            onClick={() => setIsDialogOpen(true)}
                            className="hover:cursor-pointer h-[44px] rounded-md border border-[#002FD4] flex items-center justify-center gap-[7px] px-[17px] py-[2px] text-[#002FD4]"
                        >
                            <PlusIcon size={16} weight="bold" />
                            <span className="font-poppins font-semibold text-[13px] leading-[20px] text-nowrap">
                                Create a Webinar
                            </span>
                        </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {cards.map((c) => (
                            <SingleCard key={c.id} title={c.title} value={c.value} Icon={c.Icon} />
                        ))}
                    </div>
                    <WebinarsCard />
                </div>
            </div>

            {isDialogOpen && (
                <WebinarDialog
                    isOpen={isDialogOpen}
                    onClose={() => setIsDialogOpen(false)}
                />
            )}
        </>
    )
}

export default AdminWebinar
