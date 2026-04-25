import { type FC, type ReactElement } from 'react'
import AnalyticsTab from './analytics-tab'
import { formatFee } from '@/utils/helper'

interface AnalyticsTabsProps {
    topMedical?: {
        top_symptom: string
        top_diagnosis: string
        top_lab_test: string
        top_drug: string
    }
    payment?: {
        total_payment: number
        total_cash_payment: number
        total_online_payment: number
        currency: string
    }
}

const AnalyticsTabs: FC<AnalyticsTabsProps> = ({ topMedical, payment }): ReactElement => {
    const defaults = {
        topSymptom: '—',
        topDiagnosis: '—',
        topLabTest: '—',
        topDrug: '—',
        totalPayment: '—',
        totalCash: '—',
        totalOnline: '—'
    }

    return (
        <div className='space-y-4'>
            <div className="flex items-center justify-start gap-4">
                <AnalyticsTab title="Top Symptom" data={topMedical?.top_symptom || defaults.topSymptom} />
                <AnalyticsTab title="Top Diagnosis" data={topMedical?.top_diagnosis || defaults.topDiagnosis} />
            </div>
            <div className="flex items-center justify-start gap-4">
                <AnalyticsTab title="Top Lab Test" data={topMedical?.top_lab_test || defaults.topLabTest} />
                <AnalyticsTab title="Top Drug" data={topMedical?.top_drug || defaults.topDrug} />
            </div>
            <div className="flex items-center justify-start gap-4">
                <AnalyticsTab
                    title="Total Payment"
                    data={payment ? formatFee(payment.total_payment, payment.currency) : defaults.totalPayment}
                />
                <AnalyticsTab
                    title="Total Cash Payment"
                    data={payment ? formatFee(payment.total_cash_payment, payment.currency) : defaults.totalCash}
                />
                <AnalyticsTab
                    title="Total Online Payment"
                    data={payment ? formatFee(payment.total_online_payment, payment.currency) : defaults.totalOnline}
                />
            </div>
        </div>
    )
}

export default AnalyticsTabs
