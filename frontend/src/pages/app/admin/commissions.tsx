import CommissionCards from '@/components/e-clinic/admin/commissions/commission-cards'
import CommissionsRateTable from '@/components/e-clinic/admin/commissions/commission-rate-table'
import CommissionSummaryTable from '@/components/e-clinic/admin/commissions/commission-summary-table'
import HeadSubhead from '@/components/ui/head-subhead'
import { type FC, type ReactElement } from 'react'

const CommissionsPage: FC = (): ReactElement => {
  return (
    <>
      <div className="h-screen overflow-auto bg-[#F4F6F9]">
        <div className="p-4 h-full">
          <div className="flex justify-between items-center p-6">
            <HeadSubhead
              head={'Commission Management'}
              subhead={'Configure and track commission rates for services'}
            />
          </div>
          <div className='p-4'>
            <CommissionCards />
          </div>
          <div className='p-4'>
          <CommissionsRateTable />
          <CommissionSummaryTable />
          </div>
        </div>
      </div>
    </>
  )
}

export default CommissionsPage
